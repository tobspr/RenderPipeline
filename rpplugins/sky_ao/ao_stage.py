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


class SkyAOStage(RenderStage):

    """ This is the main stage used by the Sky AO plugin, and computes
    the sky occlusion term """

    required_inputs = ["SkyAOCapturePosition"]
    required_pipes = ["SkyAOHeight", "GBuffer", "DownscaledDepth"]

    @property
    def produced_pipes(self):
        return {"SkyAO": self.blur_targets[-1].color_tex}

    def create(self):
        self.target = self.create_target("ComputeSkyAO")
        self.target.size = -2
        self.target.add_color_attachment(bits=(8, 0, 0, 0))
        self.target.prepare_buffer()

        self.target_upscale = self.create_target("UpscaleSkyAO")
        self.target_upscale.add_color_attachment(bits=(8, 0, 0, 0))
        self.target_upscale.prepare_buffer()

        self.target_upscale.set_shader_input("SourceTex", self.target.color_tex)
        self.target_upscale.set_shader_input("skipSkybox", True)
        self.target_upscale.set_shader_input("skyboxColor", Vec4(1))

        max_invalid_pixels = 8192 * 16
        self._ip_counter, self._ip_buffer = self._prepare_upscaler(max_invalid_pixels)
        self.target_upscale.set_shader_input("InvalidPixelCounter", self._ip_counter)
        self.target_upscale.set_shader_input("InvalidPixelBuffer", self._ip_buffer)

        self.target_fillin = self.create_target("FillinInvalidPixels")
        divisor = 32
        self.target_fillin.size = max_invalid_pixels // divisor, divisor
        self.target_fillin.prepare_buffer()
        self.target_fillin.set_shader_input("InvalidPixelCounter", self._ip_counter)
        self.target_fillin.set_shader_input("InvalidPixelBuffer", self._ip_buffer)
        self.target_fillin.set_shader_input("DestTex", self.target_upscale.color_tex)


        blur_passes = 1
        pixel_stretch = 1.0
        self.blur_targets = []
        current_tex = self.target_upscale.color_tex

        for i in range(blur_passes):
            target_blur_v = self.create_target("BlurV-" + str(i))
            target_blur_v.add_color_attachment(bits=(8, 0, 0, 0))
            target_blur_v.prepare_buffer()

            target_blur_h = self.create_target("BlurH-" + str(i))
            target_blur_h.add_color_attachment(bits=(8, 0, 0, 0))
            target_blur_h.prepare_buffer()

            target_blur_v.set_shader_input("SourceTex", current_tex)
            target_blur_h.set_shader_input("SourceTex", target_blur_v.color_tex)

            target_blur_v.set_shader_input("blur_direction", LVecBase2i(0, 1))
            target_blur_h.set_shader_input("blur_direction", LVecBase2i(1, 0))

            target_blur_v.set_shader_input("pixel_stretch", pixel_stretch)
            target_blur_h.set_shader_input("pixel_stretch", pixel_stretch)

            current_tex = target_blur_h.color_tex
            self.blur_targets += [target_blur_v, target_blur_h]

    def update(self):
        self._ip_counter.clear_image()

    def reload_shaders(self):
        self.target.shader = self.load_plugin_shader(
            "compute_sky_ao.frag.glsl")
        self.target_upscale.shader = self.load_plugin_shader(
            "/$$rp/shader/bilateral_upscale.frag.glsl")
        self.target_fillin.shader = self.load_plugin_shader("fillin_sky_ao.frag.glsl")

        blur_shader = self.load_plugin_shader(
            "/$$rp/shader/bilateral_blur.frag.glsl")
        for target in self.blur_targets:
            target.shader = blur_shader
