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
from rplibs.six import itervalues

class SkinShadingStage(RenderStage):

    """ This is the main stage used by the SkinShadingStage plugin """

    required_inputs = []
    required_pipes = ["ShadedScene", "GBuffer"]

    @property
    def produced_pipes(self):
        return {"ShadedScene": self.final_tex}

    def create(self):
        curr_tex = None

        for i in range(3):

            target_h = self.create_target("BlurH-" + str(i))
            target_h.add_color_attachment(bits=16)
            target_h.prepare_buffer()
            target_h.set_shader_input("direction", LVecBase2i(1, 0))
            if curr_tex is not None:
                target_h.set_shader_input("ShadedScene", curr_tex, override=True)

            curr_tex = target_h.color_tex

            target_v = self.create_target("BlurV-" + str(i))
            target_v.add_color_attachment(bits=16)
            target_v.prepare_buffer()
            target_v.set_shader_input("ShadedScene", curr_tex, override=True)
            target_v.set_shader_input("direction", LVecBase2i(0, 1))

            curr_tex = target_v.color_tex

        self.final_tex = curr_tex

    def reload_shaders(self):
        blur_shader = self.load_plugin_shader("sssss_blur.frag.glsl")
        for target in itervalues(self._targets):
            target.shader = blur_shader
