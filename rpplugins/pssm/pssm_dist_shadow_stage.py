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
from __future__ import division

from panda3d.core import Vec3, Camera, OrthographicLens, Mat4, Point4, PTAMat4
from panda3d.core import LVecBase2i

from rpcore.globals import Globals
from rpcore.render_stage import RenderStage

class PSSMDistShadowStage(RenderStage):

    """ This stage generates a depth map using Variance Shadow Maps for very
    distant objects. """

    required_inputs = []

    def __init__(self, pipeline):
        RenderStage.__init__(self, pipeline)
        self.resolution = 2048
        self.clip_size = 500
        self._sun_vector = Vec3(0, 0, 1)
        self.pta_mvp = PTAMat4.empty_array(1)
    @property
    def produced_inputs(self):
        return {"PSSMDistSunShadowMapMVP": self.pta_mvp}


    @property
    def produced_pipes(self):
        return {"PSSMDistSunShadowMap": self.target_blur_h.color_tex}

    @property
    def sun_vector(self):
        return self._sun_vector

    @sun_vector.setter
    def sun_vector(self, direction):
        self._sun_vector = direction

        distance = 4000.0
        cam_pos = Globals.base.cam.get_pos(Globals.base.render)
        self.cam_node.set_pos(cam_pos + self._sun_vector * distance)
        self.cam_node.look_at(cam_pos)
        self.cam_lens.set_film_size(self.clip_size, self.clip_size)

        # This snaps the source to its texel grids, so that there is no flickering
        # visible when the source moves. This works by projecting the
        # Point (0,0,0) to light space, compute the texcoord differences and
        # offset the light world space position by that.
        mvp = Mat4(self.mvp)
        base_point = mvp.xform(Point4(0, 0, 0, 1)) * 0.5 + 0.5
        texel_size = 1.0 / float(self.resolution)
        offset_x = base_point.x % texel_size
        offset_y = base_point.y % texel_size
        mvp.invert_in_place()
        new_base = mvp.xform(Point4(
            (base_point.x - offset_x) * 2.0 - 1.0,
            (base_point.y - offset_y) * 2.0 - 1.0,
            (base_point.z) * 2.0 - 1.0, 1))
        self.cam_node.set_pos(self.cam_node.get_pos() - Vec3(new_base.x, new_base.y, new_base.z))
        self.pta_mvp[0] = self.mvp

    @property
    def mvp(self):
        return Globals.base.render.get_transform(self.cam_node).get_mat() * \
            self.cam_lens.get_projection_mat()

    def create(self):
        self.camera = Camera("PSSMDistShadowsESM")
        self.cam_lens = OrthographicLens()
        self.cam_lens.set_film_size(12000, 12000)
        self.cam_lens.set_near_far(-1000.0, 8000.0)
        self.camera.set_lens(self.cam_lens)
        self.cam_node = Globals.base.render.attach_new_node(self.camera)

        self.target = self.create_target("ShadowMap")
        self.target.size = self.resolution
        self.target.add_depth_attachment(bits=32)
        self.target.prepare_render(self.cam_node)

        self.target_convert = self.create_target("ConvertToESM")
        self.target_convert.size = self.resolution
        self.target_convert.add_color_attachment(bits=(32, 0, 0, 0))
        self.target_convert.prepare_buffer()
        self.target_convert.set_shader_input("SourceTex", self.target.depth_tex)

        self.target_blur_v = self.create_target("BlurVert")
        self.target_blur_v.size = self.resolution
        self.target_blur_v.add_color_attachment(bits=(32, 0, 0, 0))
        self.target_blur_v.prepare_buffer()
        self.target_blur_v.set_shader_input("SourceTex", self.target_convert.color_tex)
        self.target_blur_v.set_shader_input("direction", LVecBase2i(1, 0))

        self.target_blur_h = self.create_target("BlurHoriz")
        self.target_blur_h.size = self.resolution
        self.target_blur_h.add_color_attachment(bits=(32, 0, 0, 0))
        self.target_blur_h.prepare_buffer()
        self.target_blur_h.set_shader_input("SourceTex", self.target_blur_v.color_tex)
        self.target_blur_h.set_shader_input("direction", LVecBase2i(0, 1))

        # Register shadow camera
        self._pipeline.tag_mgr.register_shadow_camera(self.camera)

    def reload_shaders(self):
        self.target_convert.shader = self.load_plugin_shader("convert_to_esm.frag.glsl")
        self.target_blur_v.shader = self.load_plugin_shader("blur_esm.frag.glsl")
        self.target_blur_h.shader = self.load_plugin_shader("blur_esm.frag.glsl")

    def set_shader_input(self, *args):
        Globals.render.set_shader_input(*args)
