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

from rpcore.render_stage import RenderStage
from panda3d.core import SamplerState, Texture

class SharpenStage(RenderStage):

    required_inputs = ["PrecomputedGrain"]
    required_pipes = ["ShadedScene"]

    def __init__(self, pipeline):
        RenderStage.__init__(self, "SharpenStage", pipeline)

    @property
    def produced_pipes(self):
        return {"ShadedScene": self._target2["color"]}

    def create(self):
        self._target = self.make_target("Sharpen")
        self._target.add_color_texture(bits=16)
        self._target.prepare_offscreen_buffer()

        self._target2 = self.make_target("Sharpen2")
        self._target2.add_color_texture(bits=16)
        self._target2.prepare_offscreen_buffer()
        self._target2.set_shader_input("ShadedScene", self._target["color"])

    def set_shader_input(self, name, *args):
        if name == "ShadedScene":
            # Make sure we sample the color texture with a linear filter
            linear_state = SamplerState()
            linear_state.set_minfilter(Texture.FT_linear)
            linear_state.set_magfilter(Texture.FT_linear)
            args = list(args) + [linear_state]
            self._target.set_shader_input(name, *args)
        else:
            RenderStage.set_shader_input(self, name, *args)

    def set_shaders(self):
        self._target.set_shader(self.load_plugin_shader("sharpen.frag.glsl"))
        self._target2.set_shader(self.load_plugin_shader("sharpen.frag.glsl"))
