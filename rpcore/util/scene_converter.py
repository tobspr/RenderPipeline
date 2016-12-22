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

import math

from panda3d.core import MaterialAttrib, GeomTristrips, CullFaceAttrib, TransparencyAttrib
from panda3d.core import SphereLight as PandaSphereLight

from rpcore.globals import Globals
from rpcore.rpobject import RPObject
from rpcore.native import SphereLight, RectangleLight, SpotLight
from rpcore.util.material_api import MaterialAPI


class SceneConverter(RPObject):
    """ Interface for converting from regular Panda3D scenes (like those imported
    from .BAM and .EGG formats) to render pipeline scenes """

    # Whether to generate the appropriate geometry for each light for
    # visualization, mostly useful for debugging
    CREATE_LIGHT_GEOMETRY = True

    # Amount in lumens to multiply the lights intensity value with. This is
    # because blender uses a different light intensity, and lights would be
    # way too dark when imported from blender otherwise
    LUMENS_CONVERSION_FACTOR = 40.0

    class ConversionResult(object):
        """ Class which returns the result of a scene conversion, reason is that
        the original lights are deleted during conversion, and so the user has no
        handle to the newly generated RP lights otherwise."""

        def __init__(self):
            self.lights = {}
            self.environment_probes = {}
            self.tristrips_converted = 0

    def __init__(self, pipeline, scene):
        """ Constructs a new converter with a given pipeline and
        a root node path """
        RPObject.__init__(self)
        self.pipeline = pipeline
        self.scene = scene
        self.result = self.ConversionResult()

    def convert(self):
        """ Prepares a given scene, by converting panda lights to render pipeline
        lights. This also converts all empties with names starting with 'ENVPROBE'
        to environment probes. Conversion of blender to render pipeline lights
        is done by scaling their intensity by LUMENS_CONVERSION_FACTOR to match lumens.

        Additionally, this finds all materials with the 'TRANSPARENT' shading
        model, and sets the proper effects on them to ensure they are rendered
        properly.

        This method also returns a result object with handles to all created
        objects, that is lights, environment probes, and transparent objects.
        This can be used to store them and process them later on, or delete
        them when a newer scene is loaded. """

        self.debug("Converting", self.scene.get_name())
        self._convert_triangle_strips()
        self._convert_lights()
        self._convert_transparent_objects()
        self.debug("Converted {} lights, {} envprobes, {} triangle strips".format(
            len(self.result.lights),
            len(self.result.environment_probes),
            self.result.tristrips_converted,
        ))
        return self.result

    def _convert_lights(self):
        """ Converts all lights """
        for light in self.scene.find_all_matches("**/+PointLight"):
            if not isinstance(light.node(), PandaSphereLight):
                self.error("Found PointLight '" + light.get_name() + "' in your scene. "
                           "Please re-export your geometry using the newest BAM Exporter "
                           "version to convert them to SphereLights")
        self._convert_sphere_lights()
        self._convert_spot_lights()
        self._convert_rectangle_lights()

    def _register_light(self, light, rp_light):
        """ Internal method to register a newly created light """
        self.pipeline.add_light(rp_light)
        if self.CREATE_LIGHT_GEOMETRY:
            self.pipeline.make_light_geometry(rp_light)
        self.result.lights[light.get_name()] = rp_light
        light.remove_node()

    def _convert_sphere_lights(self):
        """ Finds and converts all sphere lights """
        for light in self.scene.find_all_matches("**/+SphereLight"):
            light_node = light.node()
            rp_light = SphereLight()
            rp_light.pos = light.get_pos(Globals.base.render)
            rp_light.max_cull_distance = light_node.max_distance
            rp_light.intensity_lumens = self.LUMENS_CONVERSION_FACTOR * light_node.color.w
            rp_light.color = light_node.color.xyz
            rp_light.casts_shadows = light_node.shadow_caster
            rp_light.shadow_map_resolution = light_node.shadow_buffer_size.x
            rp_light.sphere_radius = light_node.radius
            self._register_light(light, rp_light)

    def _convert_spot_lights(self):
        """ Converts all spot lights """
        for light in self.scene.find_all_matches("**/+Spotlight"):
            light_node = light.node()
            rp_light = SpotLight()
            rp_light.pos = light.get_pos(Globals.base.render)
            rp_light.max_cull_distance = light_node.max_distance
            rp_light.intensity_lumens = self.LUMENS_CONVERSION_FACTOR * light_node.color.w
            rp_light.color = light_node.color.xyz
            rp_light.casts_shadows = light_node.shadow_caster
            rp_light.shadow_map_resolution = light_node.shadow_buffer_size.x
            rp_light.fov = light_node.exponent / math.pi * 180.0
            direction = light.get_mat(Globals.base.render).xform_vec((0, 0, -1))
            rp_light.direction = direction
            self._register_light(light, rp_light)

    def _convert_rectangle_lights(self):
        """ Converts all rectangle lights """
        for light in self.scene.find_all_matches("**/+RectangleLight"):
            light_node = light.node()
            rp_light = RectangleLight()
            rp_light.pos = light.get_pos(Globals.base.render)
            rp_light.max_cull_distance = light_node.max_distance
            rp_light.intensity_lumens = self.LUMENS_CONVERSION_FACTOR * light_node.color.w
            rp_light.color = light_node.color.xyz
            rp_light.casts_shadows = light_node.shadow_caster
            rp_light.shadow_map_resolution = light_node.shadow_buffer_size.x
            rp_light.up_vector = light.get_mat(Globals.base.render).xform_vec((0, 0, 0.5))
            rp_light.right_vector = light.get_mat(Globals.base.render).xform_vec((0, 0.5, 0))
            self._register_light(light, rp_light)

    def _convert_environment_probes(self):
        """ Converts all empties named ENVPROBE_? to environment probes """
        have_envmaps = self.pipeline.plugin_mgr.is_plugin_enabled("env_probes")
        if not have_envmaps:
            self.debug("Not creating any environment probe, because the env_probes plugin is not enabled")

        for node_path in self.scene.find_all_matches("**/ENVPROBE*"):
            if have_envmaps:
                probe = self.pipeline.add_environment_probe()
                probe.set_mat(node_path.get_mat())
                probe.border_smoothness = 0.0001  # XXX: Find a way to export it
                probe.parallax_correction = True
                self.result.environment_probes[node_path.get_name()] = probe
            node_path.remove_node()

    def _emit_tristrip_warning(self, node_name):
        """ Internal method to emit the warning about converting triangle strips """
        self.warn("At least one GeomNode ('" + str(node_name) + "' and possibly more..) contains tristrips.")
        self.warn("Due to a NVIDIA Driver bug, we have to convert them to triangles now.")
        self.warn("Consider exporting your models with the Bam Exporter to avoid this.")

    def _convert_triangle_strips(self):
        """ Converts all triangle strips found in the scene, because some nvidia
        drivers don't handle them properly """
        warning_emitted = False
        for geom_np in self.scene.find_all_matches("**/+GeomNode"):
            geom_node = geom_np.node()
            geom_count = geom_node.get_num_geoms()
            for i in range(geom_count):
                state = geom_node.get_geom_state(i)
                geom = geom_node.get_geom(i)
                needs_conversion = False

                # Check if this geom contains any GeomTristrips
                for prim in geom.get_primitives():
                    if isinstance(prim, GeomTristrips):
                        needs_conversion = True
                        if not warning_emitted:
                            self._emit_tristrip_warning(geom_node.get_name())
                            warning_emitted = True
                            self.result.tristrips_converted += 1
                            break

                # Convert (decompose) in case any tristrip primitive was found
                if needs_conversion:
                    geom_node.modify_geom(i).decompose_in_place()

                # Warning about unassigned materials
                if not state.has_attrib(MaterialAttrib):
                    self.error("Geom '" + str(geom_node.get_name()) + "' on node path "
                               "'" + geom_np.get_name() + "' has no material! Please "
                               "assign a material.")

    def _convert_transparent_objects(self):
        """ Sets the appropriate effect on all models with the transparent shading
        model """
        for geom_np in self.scene.find_all_matches("**/+GeomNode"):
            geom_node = geom_np.node()
            geom_count = geom_node.get_num_geoms()
            for i in range(geom_count):
                state = geom_node.get_geom_state(i)

                # Get material, and extract its shading model
                material_attrib = state.get_attrib(MaterialAttrib)
                if not material_attrib or not material_attrib.get_material():
                    self.error("Geom '" + str(geom_np.get_name()) + "' has a material "
                               "attrib, but no material assigned!")
                    continue
                material = material_attrib.get_material()
                shading_model = MaterialAPI.get_shading_model(material)

                if shading_model in MaterialAPI.TRANSPARENT_MODELS:
                    if geom_count > 1:
                        self.error("Transparent materials must be on their own geom! "
                                   "If you are exporting from blender, split them into "
                                   "seperate meshes, then re-export your scene. The "
                                   "problematic mesh is: '" + str(geom_np.get_name()) + "'")
                        continue

                    self.pipeline.set_effect(
                        geom_np, "effects/default.yaml",
                        {
                            "render_forward": True,
                            "render_forward_prepass": shading_model == MaterialAPI.SM_TRANSPARENT_GLASS,
                            "render_gbuffer": False,
                            "render_shadow": True
                        }, 100)

                    if shading_model == MaterialAPI.SM_TRANSPARENT_GLASS:
                        geom_np.set_attrib(CullFaceAttrib.make(CullFaceAttrib.M_cull_none), 1000)
                    
                    geom_np.set_attrib(TransparencyAttrib.make(TransparencyAttrib.M_alpha), 1000)
                    geom_np.set_bin("transparent", 0)
