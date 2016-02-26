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

from panda3d.core import Vec3, Camera, OrthographicLens, PTAMat4, SamplerState

from rpcore.globals import Globals
from rpcore.render_stage import RenderStage

class PSSMSceneShadowStage(RenderStage):

    """ This stage creates the shadow map which covers the whole important part
    of the scene. This is required because the shadow cascades only cover the
    view frustum, but many plugins (VXGI, EnvMaps) require a shadow map. """

    required_inputs = []
    required_pipes = []

    def __init__(self, pipeline):
        RenderStage.__init__(self, pipeline)
        self.resolution = 2048
        self._sun_vector = Vec3(0, 0, 1)
        self._pta_mvp = PTAMat4.empty_array(1)

    @property
    def produced_inputs(self):
        return {"PSSMSceneSunShadowMVP": self._pta_mvp}

    @property
    def produced_pipes(self):
        return {"PSSMSceneSunShadowMapPCF": (self._target['depth'], self.make_pcf_state())}

    def make_pcf_state(self):
        state = SamplerState()
        state.set_minfilter(SamplerState.FT_shadow)
        state.set_magfilter(SamplerState.FT_shadow)
        return state

    @property
    def sun_vector(self):
        return self._sun_vector

    @sun_vector.setter
    def sun_vector(self, direction):
        self._sun_vector = direction

        distance = 400.0
        cam_pos = Globals.base.cam.get_pos(Globals.base.render)
        self._cam_node.set_pos(cam_pos + self._sun_vector * distance)
        self._cam_node.look_at(cam_pos)

        # Compute MVP
        transform = Globals.base.render.get_transform(self._cam_node).get_mat()
        self._pta_mvp[0] = transform * self._cam_lens.get_projection_mat()

    def create(self):

        self._camera = Camera("PSSMSceneSunShadowCam")
        self._cam_lens = OrthographicLens()
        self._cam_lens.set_film_size(400, 400)
        self._cam_lens.set_near_far(0.0, 800.0)
        self._camera.set_lens(self._cam_lens)
        self._cam_node = Globals.base.render.attach_new_node(self._camera)

        self._target = self.make_target("ShadowMap")
        self._target.set_source(self._cam_node, Globals.base.win)
        self._target.size = self.resolution
        self._target.add_depth_texture(bits=32)
        self._target.create_overlay_quad = False
        self._target.color_write = False
        self._target.prepare_scene_render()

        # Register shadow camera
        self._pipeline.tag_mgr.register_shadow_camera(self._camera)

    def set_shader_input(self, *args):
        Globals.render.set_shader_input(*args)
