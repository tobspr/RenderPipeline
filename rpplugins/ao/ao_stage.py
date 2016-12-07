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

from panda3d.core import LVecBase2i, Vec4
from rpcore.render_stage import RenderStage
from rpcore.util.bilateral_upscaler import BilateralUpscaler


class AOStage(RenderStage):

    required_inputs = []
    required_pipes = ["GBuffer", "LowPrecisionDepth", "LowPrecisionHalfresDepth", "PreviousFrame::ResolvedAO[RG8,50%]",
                      "CombinedVelocity", "LowPrecisionHalfresNormals", "LowPrecisionNormals",
                      "PreviousFrame::SceneDepth[R32I]"]

    @property
    def produced_pipes(self):
        return {
            "AmbientOcclusion": self.target_detail_ao.color_tex if self.enable_small_scale_ao else self.upscaler.result_tex,
            "ResolvedAO": self.target_resolve.color_tex
            }
    def create(self):

        # XXX: Use RG8 when not using sky ao
        ao_bits = (8, 8, 0, 0)

        # Target to compute the initial ao
        self.target = self.create_target("SampleAO")
        self.target.size = "50%"
        self.target.add_color_attachment(bits=ao_bits)
        self.target.prepare_buffer()

        # Construct the temporal resolve target
        self.target_resolve = self.create_target("ResolveAO")
        self.target_resolve.size = "50%"
        self.target_resolve.add_color_attachment(bits=ao_bits)
        self.target_resolve.prepare_buffer()
        self.target_resolve.set_shader_input("CurrentTex", self.target.color_tex)

        self.debug("Blur quality is", self.quality)

        if self.quality == "LOW":
            # pixel_stretch = 2.0
            pixel_stretch = 1.0
            blur_passes = 1
        elif self.quality == "MEDIUM":
            pixel_stretch = 1.0
            blur_passes = 2
        elif self.quality == "HIGH":
            pixel_stretch = 1.0
            blur_passes = 3
        elif self.quality == "ULTRA":
            pixel_stretch = 1.0
            blur_passes = 5
        else:
            self.fatal("Unkown blur quality")

        # Create N blur passes (each horizontal/vertical) which smooth out the result 
        self.blur_targets = []
        current_tex = self.target_resolve.color_tex

        for i in range(blur_passes):

            for name, direction in [("V", LVecBase2i(0, 1)), ("H", LVecBase2i(1, 0))]:
                target_blur = self.create_target("AOBlur" + name + "-" + str(i))
                target_blur.add_color_attachment(bits=ao_bits)
                target_blur.size = "50%"
                target_blur.prepare_buffer()
                target_blur.set_shader_input("SourceTex", current_tex)
                target_blur.set_shader_input("blur_direction", direction)
                target_blur.set_shader_input("pixel_stretch", pixel_stretch)

                current_tex = target_blur.color_tex
                self.blur_targets.append(target_blur)

        # Upscale from half to full-resolution
        self.upscaler = BilateralUpscaler(
            self,
            halfres=False,
            source_tex=current_tex,
            name=self.stage_id + ":Upscale",
            percentage=0.05,
            bits=ao_bits,
            fillin=False
        )

        # Optionally compute small scale (detailed) ao
        if self.enable_small_scale_ao:
            self.target_detail_ao = self.create_target("SmallScaleDetailAO")
            self.target_detail_ao.add_color_attachment(bits=ao_bits)
            self.target_detail_ao.prepare_buffer()
            self.target_detail_ao.set_shader_input("AOResult", self.upscaler.result_tex)


    def update(self):
        self.upscaler.update()

    def set_dimensions(self):
        self.upscaler.set_dimensions()

    def reload_shaders(self):
        self.target.shader = self.load_plugin_shader("ao_sample.frag.glsl")
        self.upscaler.set_shaders(
            upscale_shader=self.load_plugin_shader("upscale_ao.frag.glsl")
        )

        blur_shader = self.load_plugin_shader(
            "/$$rp/shader/bilateral_halfres_blur.frag.glsl")

        for target in self.blur_targets:
            target.shader = blur_shader
        if self.enable_small_scale_ao:
            self.target_detail_ao.shader = self.load_plugin_shader("small_scale_ao.frag.glsl")

        self.target_resolve.shader = self.load_plugin_shader("resolve_ao.frag.glsl")
