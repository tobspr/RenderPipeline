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

from .. import *

class ScatteringEnvmapStage(RenderStage):

    """ This stage uses the precomputed data to make a cubemap containing the
    scattering """

    required_pipes = []
    required_inputs = ["DefaultSkydome"]

    def __init__(self, pipeline):
        RenderStage.__init__(self, "ScatteringEnvmapStage", pipeline)

    @property
    def produced_pipes(self):
        return {
            "ScatteringIBLDiffuse": self._filter.diffuse_cubemap,
            "ScatteringIBLSpecular": self._filter.specular_cubemap,
        }

    def create(self):
        self._filter = self.make_cubemap_filter("Filter")

        self._target_cube = self.make_target("Compute")
        self._target_cube.size = self._filter.size * 6, self._filter.size
        self._target_cube.prepare_offscreen_buffer()
        self._target_cube.set_shader_input("DestCubemap", self._filter.target_cubemap)
        self._filter.create()

        # Make the stages use our cubemap
        ambient_stage = get_internal_stage("ambient_stage", "AmbientStage")
        ambient_stage.required_pipes.append("ScatteringIBLDiffuse")
        ambient_stage.required_pipes.append("ScatteringIBLSpecular")

        gbuffer_stage = get_internal_stage("gbuffer_stage", "GBufferStage")
        gbuffer_stage.required_pipes.append("ScatteringIBLDiffuse")
        gbuffer_stage.required_pipes.append("ScatteringIBLSpecular")

    def set_shaders(self):
        self._target_cube.set_shader(self.load_plugin_shader("scattering_envmap.frag.glsl"))
        self._filter.set_shaders()
