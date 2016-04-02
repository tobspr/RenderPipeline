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

from panda3d.core import PTAInt
from rpcore.render_stage import RenderStage

class PSSMStage(RenderStage):

    """ This stage uses the PSSM Shadow map to render the shadows """

    required_inputs = []
    required_pipes = ["ShadedScene", "PSSMShadowAtlas", "GBuffer", "PSSMShadowAtlasPCF"]

    @property
    def produced_pipes(self):
        return {"ShadedScene": self.void_target.color_tex}

    def create(self):

        # Store whether the target is active
        self.pta_active = PTAInt.empty_array(1)

        self.target = self.create_target("ApplyPSSM")
        self.target.add_color_attachment(bits=16)
        self.target.prepare_buffer()

        self.void_target = self.create_target("PSSMVoidShader")
        self.void_target.add_color_attachment(bits=16)
        self.void_target.prepare_buffer()
        self.void_target.activ = False
        self.void_target.set_shader_input("SourcePSSMTex", self.target.color_tex)
        self.void_target.set_shader_input("usePssmTex", self.pta_active)

    def set_render_shadows(self, render_shadows):
        """ Toggle whether to render shadows or whether to just pass through
        the scene color """
        self.pta_active[0] = int(render_shadows)
        self.target.active = render_shadows

    def reload_shaders(self):
        self.target.shader = self.load_plugin_shader("apply_pssm_shadows.frag.glsl")
        self.void_target.shader = self.load_plugin_shader("pass_through_shader.frag.glsl")
