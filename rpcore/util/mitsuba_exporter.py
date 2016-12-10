"""

RenderPipeline

Copyright (c) 2014-2016 tobspr <tobias.springer1@gmail.com>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

"""

import os

from direct.stdpy.file import isfile, isdir, join
from panda3d.core import GeomVertexReader, Mat4, Vec3, Vec4
from panda3d.core import PNMImage, TransformState, MaterialAttrib, TextureAttrib, SamplerState

from rpcore.rpobject import RPObject
from rpcore.globals import Globals
from rpcore.native import PointLight, SpotLight

def to_safe_name(name):
    """ Converts a string to a valid filename """
    return name.replace("\\", "").replace("/", "").replace(" ", "_").replace(":", "")

def vec2xml(v):
    """ Converts a vector to a valid xml string """
    return "{:.8f}, {:.8f}, {:.8f}".format(*v) 

def color2xml(v):
    """ Converts a color to a valid xml string """
    return "{:.8f}, {:.8f}, {:.8f}".format(*[max(i, 0.0001) for i in v]) 


class MitsubaExporter(RPObject):
    """ Helper class to export scenes to mitsuba """

    TRANSFORM_CS = Mat4.ident_mat()

    def __init__(self, pipeline):
        """ Constructs a new exporter """
        RPObject.__init__(self)
        self.pipeline = pipeline
        self.export_objects = {}
        self.export_states = {}

    def add(self, nodepath):
        """ Adds a new nodepath to export """
        self.debug("Adding", nodepath)
        geom_id = 0
        for np in nodepath.find_all_matches("**/*"):
            if "skybox" in np.get_name().lower():
                self.debug("Skipping skybox")
                continue
            self.debug("Adding", np.get_name())
            for geom_np in np.find_all_matches("**/+GeomNode"):
                geom_node = geom_np.node()
                transform = geom_np.get_transform(Globals.base.render)
                for i in range(geom_node.get_num_geoms()):
                    name = to_safe_name("obj-" + np.get_name() + "-GN" + geom_np.get_name() + "-" + str(geom_id) + "-Geom" + str(i) + ".obj")
                    geom, state = geom_node.get_geom(i), geom_node.get_geom_state(i)
                    self._add_geom(name, geom, state, transform)
                geom_id += 1
        
    def _add_geom(self, name, geom, state, transform):
        """ Adds a geom and state to the list of geoms to get exported """
        if geom.get_num_primitives() != 1:
            self.error("Unsupported geom with more/less than 1 GeomPrimitive:", name)
            return

        content = ["o Object"]
        mat = transform.get_mat()

        tpose_world_to_model = Mat4(mat)
        tpose_world_to_model.invert_in_place()
        tpose_world_to_model.transpose_in_place()

        # Convert to GeomTriangles for easier processing
        primitive = geom.get_primitive(0).decompose()

        # Get reader for vertices and normals
        vtx_data = geom.get_vertex_data()
        
        vtx_reader = GeomVertexReader(vtx_data, "vertex")
        vtx_column = vtx_reader.get_column()

        nrm_reader = GeomVertexReader(vtx_data, "normal")
        nrm_column = nrm_reader.get_column()

        tc_reader = GeomVertexReader(vtx_data, "texcoord")
        tc_column = tc_reader.get_column()
        

        # Sanity checks
        if not vtx_column or vtx_column.get_num_values() != 3:
            self.error("Unsupported geom with vertex not being 3f:", name)
            return
        
        if not nrm_column or nrm_column.get_num_values() != 3:
            self.error("Unsupported geom with normal not being 3f:", name)
            return
        
        if not tc_column or tc_column.get_num_values() != 2:
            self.error("Unsupported geom with texcoord not being 2f:", name)
            return

        # Add vertices
        while not vtx_reader.isAtEnd():
            pos = vtx_reader.get_data3f()
            tpos = mat.xform(Vec4(pos, 1)).xyz
            content.append("v {:3.5f} {:3.5f} {:3.5f}".format(*tpos))

        # Add normals
        while not nrm_reader.isAtEnd():
            nrm = Vec4(nrm_reader.get_data3f(), 0)
            tnrm = tpose_world_to_model.xform(nrm).xyz
            # tnrm = nrm.xyz
            content.append("vn {:3.5f} {:3.5f} {:3.5f}".format(*tnrm))

        # Add texture coordinates
        while not tc_reader.isAtEnd():
            tc = tc_reader.get_data2f()
            content.append("vt {:3.5f} {:3.5f}".format(*tc))

        # Export primitives
        for i in range(0, primitive.get_num_vertices(), 3):
            vertices = (primitive.get_vertex(i + 0) + 1,
                        primitive.get_vertex(i + 1) + 1,
                        primitive.get_vertex(i + 2) + 1)
                        
            content.append("f {0}/{0}/{0} {1}/{1}/{1} {2}/{2}/{2}".format(*vertices))

        self.export_objects[name] = content
        self.export_states[name] = (state, transform)

    def _generate_transform(self, transform, is_cam=False):
        fwd = transform.get_mat().xform(Vec3(0, 1, 0))
        return "<lookat target='{}' origin='{}' up='{}'/>".format(
            vec2xml(fwd + transform.get_pos()), vec2xml(transform.get_pos()), "0, 0, 1")
        
    def _generate_xml_for_tex(self, tex, start_path):
        """ Generates the xml string for a given texture """
        output = []
        
        def get_wrap(wrap):
            return {
                SamplerState.WM_clamp: "clamp",
                SamplerState.WM_repeat: "repeat",
                SamplerState.WM_mirror: "mirror"
            }.get(wrap, "repeat")

        texfilter = "ewa"
        if tex.get_magfilter() == SamplerState.FT_nearest:
            texfilter = "nearest"

        fullpath = tex.get_fullpath().to_os_specific()
        relpath = os.path.relpath(fullpath, start=start_path).replace("\\", "/")
        add = output.append
        add("<texture name='diffuseReflectance' type='bitmap'>")
        add("    <string name='filename' value='{}' />".format(relpath))
        add("    <string name='filterType' value='{}' />".format(texfilter))
        add("    <string name='wrapModeU' value='{}' />".format(get_wrap(tex.get_wrap_u())))
        add("    <string name='wrapModeV' value='{}' />".format(get_wrap(tex.get_wrap_v())))
        add("</texture>")
        return output


    def _generate_output(self, path):
        """ Generates the mitsuba xml file """
        output = []
        cam_lens = Globals.base.camLens
        cam_transform = Globals.base.camera.get_transform(Globals.base.render)

        add = output.append
        add("<?xml version='1.0' encoding='utf-8'?>")
        add("<scene version='0.5.0'>")
        add("    <sensor type='perspective'>")
        add("        <float name='farClip' value='{}'/>".format(cam_lens.get_far()))
        add("        <float name='focusDistance' value='3.0'/>")
        add("        <float name='fov' value='{}'/>".format(cam_lens.get_fov().x))
        add("        <string name='fovAxis' value='x'/>")
        add("        <float name='nearClip' value='{}'/>".format(cam_lens.get_near()))
        add("        <transform name='toWorld'>")
        add("            " + self._generate_transform(cam_transform, True))
        add("        </transform>")
        add("        <sampler type='ldsampler'>")
        add("            <integer name='sampleCount' value='64'/>")
        add("        </sampler>")
        add("        <film type='hdrfilm'>")
        add("            <boolean name='banner' value='false'/>")
        # add("            <string name='fileFormat' value='png'/>")
        # add("            <string name='pixelFormat' value='rgb'/>")
        add("            <integer name='width' value='{}'/>".format(Globals.base.win.get_x_size()))
        add("            <integer name='height' value='{}'/>".format(Globals.base.win.get_y_size()))
        add("            <rfilter type='box'/>")
        add("        </film>")
        add("    </sensor>")
        add("   <integrator type='path'>")
        add("       <integer name='maxDepth' value='5' />")
        add("   </integrator>")

        add("<emitter type='envmap'>")
        add("    <string name='filename' value='_envmap.png' />") 
        add("    <float name='gamma' value='1.0' />")
        add("</emitter>")

        self.debug("Exporting lights ..")
        for light in self.pipeline.light_mgr.all_lights:
            print(light)
            if isinstance(light, PointLight):
                pos = light.pos
                add("<shape type='sphere'>")
                add("  <point name='center' x='{}' y='{}' z='{}' />".format(*pos))
                add("  <float name='radius' value='{}' />".format(light.inner_radius))
                add("  <emitter type='area'>")
                add("    <rgb name='radiance' value='" + color2xml(light.color * light.energy) + "' />")
                add("  </emitter>")
                add("</shape>")


        self.debug("Exporting materials ..")
        for obj_filename, (state, transform) in self.export_states.items():

            material_attrib = state.get_attrib(MaterialAttrib)
            if not material_attrib:
                self.warn("Skipping", obj_filename, "since no material is present!")
                continue
            material = material_attrib.get_material()

            texture_attrib = state.get_attrib(TextureAttrib)
            if not texture_attrib:
                self.warn("Skipping", obj_filename, "since no texture attrib is present!")
                continue

            diff_tex = texture_attrib.get_on_texture(texture_attrib.get_on_stage(0))
            rough_tex = texture_attrib.get_on_texture(texture_attrib.get_on_stage(3))

            metallic = material.get_metallic() > 0.5

            add("<shape type='obj'>")
            add("  <string name='filename' value='{}' />".format(obj_filename))

            if metallic:
                add("  <bsdf type='roughconductor'>")
                add("    <string name='material' value='Ag' />")
            else:
                add("  <bsdf type='roughplastic'>")
                add("    <float name='intIOR' value='{}'/>".format(material.get_refractive_index()))

            add("    <string name='distribution' value='ggx'/>")

            reflectance = "specular" if metallic else "diffuse"
            
            add("    <texture name='{}Reflectance' type='scale'>".format(reflectance))
            output += self._generate_xml_for_tex(diff_tex, path)
            add("      <rgb name='scale' value='{}' />".format(vec2xml(material.get_base_color())))
            add("    </texture>")

            # add("            <texture name='alpha' type='scale'>")
            # output += self._generate_xml_for_tex(rough_tex, path)
            # add("                <rgb name='scale' value='{}' />".format(material.get_roughness() ** 2))
            # add("            </texture>")

            add("    <float name='alpha' value='{}'/>".format(material.get_roughness() ** 2)) # uses disney roughness
            add("  </bsdf>")
            add("</shape>")

        add("</scene>")
        return output

    def write(self, path):
        """ Writes out the generated objects """
        if not isdir(path):
            os.makedirs(path)

        # Write all dependend objects
        for name, contents in self.export_objects.items():
            with open(join(path, name), "w") as handle:
                for line in contents:
                    handle.write(line + "\n")

        # Write mitsuba xml file
        output = self._generate_output(path)
        with open(join(path, "scene.xml"), "w") as handle:
            for line in output:
                handle.write(line + "\n")


        # Write batch file to run Mitsuba
        with open(join(path, "run_mitsuba.bat"), "w") as handle:
            handle.write("@echo off\n")
            handle.write("C:/mitsuba/mitsuba -p 6 scene.xml\n")
            handle.write("C:/mitsuba/mtsutil tonemap scene.exr\n")
            handle.write("del mitsuba.*.log\n")
            handle.write("pause\n")

        # Write a grey environment map
        envmap = PNMImage(32, 16, 3, 2**16 - 1)
        envmap.fill(1.0 / 2**16)
        envmap.write(join(path, "_envmap.png"))

        self.debug("Done.")
