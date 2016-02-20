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

from panda3d.core import LVecBase2i
from rpcore.render_stage import RenderStage

class AOStage(RenderStage):

    required_pipes = ["GBuffer"]
    required_inputs = ["Noise4x4"]

    def __init__(self, pipeline):
        RenderStage.__init__(self, "AOStage", pipeline)

    @property
    def produced_pipes(self):
        return {"AmbientOcclusion": self._target_upscale['color']}

    def create(self):
        self._target = self.make_target("Sample")
        self._target.set_half_resolution()
        self._target.add_color_texture(bits=8)
        self._target.has_color_alpha = True
        self._target.prepare_offscreen_buffer()
        self._target.quad.set_instance_count(4)

        self._target_merge = self.make_target("Merge")
        self._target_merge.set_half_resolution()
        self._target_merge.add_color_texture(bits=8)
        self._target_merge.has_color_alpha = True
        self._target_merge.prepare_offscreen_buffer()

        self._target_blur_v = self.make_target("BlurV")
        self._target_blur_v.set_half_resolution()
        self._target_blur_v.add_color_texture(bits=8)
        self._target_blur_v.has_color_alpha = True
        self._target_blur_v.prepare_offscreen_buffer()

        self._target_blur_h = self.make_target("BlurH")
        self._target_blur_h.set_half_resolution()
        self._target_blur_h.add_color_texture(bits=8)
        self._target_blur_h.has_color_alpha = True
        self._target_blur_h.prepare_offscreen_buffer()

        self._target_upscale = self.make_target("Upscale")
        self._target_upscale.add_color_texture(bits=8)
        self._target_upscale.has_color_alpha = True
        self._target_upscale.prepare_offscreen_buffer()

        self._target_upscale.set_shader_input("SourceTex", self._target_blur_h["color"])
        self._target_blur_v.set_shader_input("SourceTex", self._target_merge["color"])
        self._target_blur_h.set_shader_input("SourceTex", self._target_blur_v["color"])

        self._target_blur_v.set_shader_input("blur_direction", LVecBase2i(0, 1))
        self._target_blur_h.set_shader_input("blur_direction", LVecBase2i(1, 0))

        self._target_merge.set_shader_input("SourceTex", self._target["color"])

    def set_shaders(self):
        self._target.set_shader(self.load_plugin_shader(
            "$$shader/sample_halfres_interleaved.vert.glsl", "ao_sample.frag.glsl"))
        self._target_upscale.set_shader(self.load_plugin_shader(
            "$$shader/bilateral_upscale.frag.glsl"))
        self._target_merge.set_shader(self.load_plugin_shader(
            "$$shader/merge_interleaved_target.frag.glsl"))

        blur_shader = self.load_plugin_shader(
            "$$shader/bilateral_halfres_blur.frag.glsl")
        self._target_blur_v.set_shader(blur_shader)
        self._target_blur_h.set_shader(blur_shader)
