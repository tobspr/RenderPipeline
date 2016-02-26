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

from rpcore.render_stage import RenderStage

class FXAAStage(RenderStage):

    """ This is the main stage used by the FXAA plugin """

    required_pipes = ["ShadedScene", "GBuffer"]
    required_inputs = []

    @property
    def produced_pipes(self):
        return {"ShadedScene": self._target["color"]}

    def create(self):

        self._luma_target = self.make_target("FXAAWriteLuma")
        self._luma_target.add_color_texture(bits=16)
        self._luma_target.has_color_alpha = True
        self._luma_target.prepare_offscreen_buffer()

        self._target = self.make_target("FXAA")
        self._target.add_color_texture(bits=16)
        self._target.prepare_offscreen_buffer()
        self._target.set_shader_input("SourceTex", self._luma_target["color"])

    def set_shaders(self):
        self._target.set_shader(self.load_plugin_shader("fxaa_stage.frag.glsl"))
        self._luma_target.set_shader(self.load_plugin_shader("write_luma.frag.glsl"))
