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

from ...render_stage import RenderStage
from panda3d.core import SamplerState, Vec4

class ColorCorrectionStage(RenderStage):

    required_inputs = ["PrecomputedGrain"]
    required_pipes = ["ShadedScene"]

    def __init__(self, pipeline):
        RenderStage.__init__(self, "ColorCorrectionStage", pipeline)
        self._use_sharpen = False

    def set_use_sharpen(self, flag):
        self._use_sharpen = flag

    def create(self):
        self._target = self.make_target("MainTonemap")

        # Create the sharpen target
        if self._use_sharpen:

            # When using a sharpen filter, the main target needs a color texture
            self._target.add_color_texture(bits=8)
            self._target.prepare_offscreen_buffer()

            self._target_sharpen = self.make_target("Sharpen")
            # We don't have a color attachment, but still want to write color
            self._target_sharpen.color_write = True
            self._target_sharpen.prepare_offscreen_buffer()
            self._target_sharpen.make_main_target()

            # Use a linear filter for the color texture, this is required for the sharpen
            # filter to work properly.
            self._target["color"].set_minfilter(SamplerState.FT_linear)
            self._target["color"].set_magfilter(SamplerState.FT_linear)

            self._target_sharpen.set_shader_input("SourceTex", self._target["color"])

        else:
            # Make the main target the only target
            self._target.color_write = True
            self._target.prepare_offscreen_buffer()
            self._target.make_main_target()

    def set_shaders(self):
        self._target.set_shader(self.load_plugin_shader("correct_color.frag.glsl"))
        if self._use_sharpen:
            self._target_sharpen.set_shader(self.load_plugin_shader("sharpen.frag.glsl"))
