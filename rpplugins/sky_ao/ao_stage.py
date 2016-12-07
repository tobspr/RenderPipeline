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

from panda3d.core import Vec4, LVecBase2i

from rpcore.render_stage import RenderStage
from rpcore.util.bilateral_upscaler import BilateralUpscaler

class SkyAOStage(RenderStage):

    """ This is the main stage used by the Sky AO plugin, and computes
    the sky occlusion term """

    required_inputs = ["SkyAOCapturePosition"]
    required_pipes = ["SkyAOHeight", "GBuffer", "LowPrecisionDepth"]

    @property
    def produced_pipes(self):
        return {"SkyAOHalfRes": self.halfres_upscaler.result_tex}

    def create(self):
        self.target = self.create_target("ComputeSkyAO")
        self.target.size = "25%"
        self.target.add_color_attachment(bits=(8, 0, 0, 0))
        self.target.prepare_buffer()

        self.halfres_upscaler = BilateralUpscaler(
            self,
            halfres=True,
            source_tex=self.target.color_tex,
            name=self.stage_id + ":UpscaleHalf",
            percentage=0.02,
            bits=(8, 0, 0, 0))

    def update(self):
        # self.fullres_upscaler.update()
        self.halfres_upscaler.update()

    def set_dimensions(self):
        # self.fullres_upscaler.set_dimensions()
        self.halfres_upscaler.set_dimensions()

    def reload_shaders(self):
        self.target.shader = self.load_plugin_shader(
            "compute_sky_ao.frag.glsl")

        self.halfres_upscaler.set_shaders(
            upscale_shader=self.load_plugin_shader("upscale_sky_ao_half.frag.glsl"),
            fillin_shader=self.load_plugin_shader("fillin_sky_ao.frag.glsl"),
        )

        # self.fullres_upscaler.set_shaders(
        #     upscale_shader=self.load_plugin_shader("upscale_sky_ao.frag.glsl"),
        #     fillin_shader=self.load_plugin_shader("fillin_sky_ao.frag.glsl"),
        # )

        # self.target_resolve.shader = self.load_plugin_shader("resolve_sky_ao.frag.glsl")

        # blur_shader = self.load_plugin_shader(
        #     "/$$rp/shader/bilateral_halfres_blur.frag.glsl")

        # for target in self.blur_targets:
        #     target.shader = blur_shader
