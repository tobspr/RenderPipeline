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
    required_pipes = ["SkyAOHeight", "GBuffer", "DownscaledDepth", "LowPrecisionNormals",
                      "PreviousFrame::SkyAO", "PreviousFrame::SceneDepth",
                      "CombinedVelocity"]

    @property
    def produced_pipes(self):
        return {"SkyAO": self.target_resolve.color_tex}

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
            percentage=0.02)

        blur_passes = 1
        self.blur_targets = []
        current_tex = self.halfres_upscaler.result_tex

        for i in range(blur_passes):
            target_blur_v = self.create_target("BlurV-" + str(i))
            target_blur_v.add_color_attachment(bits=(8, 0, 0, 0))
            target_blur_v.size = "50%"
            target_blur_v.prepare_buffer()

            target_blur_h = self.create_target("BlurH-" + str(i))
            target_blur_h.add_color_attachment(bits=(8, 0, 0, 0))
            target_blur_h.size = "50%"
            target_blur_h.prepare_buffer()

            target_blur_v.set_shader_input("SourceTex", current_tex)
            target_blur_h.set_shader_input("SourceTex", target_blur_v.color_tex)

            target_blur_v.set_shader_input("blur_direction", LVecBase2i(0, 1))
            target_blur_h.set_shader_input("blur_direction", LVecBase2i(1, 0))

            current_tex = target_blur_h.color_tex
            self.blur_targets += [target_blur_v, target_blur_h]

        self.fullres_upscaler = BilateralUpscaler(
            self,
            source_tex=current_tex,
            name=self.stage_id + ":UpscaleFull",
            percentage=0.05
        )


        self.target_resolve = self.create_target("ResolveSkyAO")
        self.target_resolve.add_color_attachment(bits=(8, 0, 0, 0))
        self.target_resolve.prepare_buffer()
        self.target_resolve.set_shader_input("CurrentTex", self.fullres_upscaler.result_tex)

    def update(self):
        self.fullres_upscaler.update()
        self.halfres_upscaler.update()

    def set_dimensions(self):
        self.fullres_upscaler.set_dimensions()
        self.halfres_upscaler.set_dimensions()

    def reload_shaders(self):
        self.target.shader = self.load_plugin_shader(
            "compute_sky_ao.frag.glsl")

        self.halfres_upscaler.set_shaders(
            upscale_shader=self.load_plugin_shader("upscale_sky_ao_half.frag.glsl"),
            fillin_shader=self.load_plugin_shader("fillin_sky_ao.frag.glsl"),
        )
        self.fullres_upscaler.set_shaders(
            upscale_shader=self.load_plugin_shader("upscale_sky_ao.frag.glsl"),
            fillin_shader=self.load_plugin_shader("fillin_sky_ao.frag.glsl"),
        )

        self.target_resolve.shader = self.load_plugin_shader("resolve_sky_ao.frag.glsl")

        blur_shader = self.load_plugin_shader(
            "/$$rp/shader/bilateral_halfres_blur.frag.glsl")

        for target in self.blur_targets:
            target.shader = blur_shader
