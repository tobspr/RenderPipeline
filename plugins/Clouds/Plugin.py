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
# Load the plugin api
from .. import *

from panda3d.core import SamplerState
from CloudStage import CloudStage

class Plugin(BasePlugin):

    @PluginHook("on_stage_setup")
    def setup_stages(self):
        self._stage = self.create_stage(CloudStage)

    @PluginHook("on_pipeline_created")
    def setup_inputs(self):
        sprite_tex = Globals.loader.loadTexture(self.get_resource("CloudSprites.png"))
        noise_tex = Globals.loader.loadTexture(self.get_resource("Noise.png"))

        for tex in [sprite_tex, noise_tex]:
            tex.set_wrap_u(SamplerState.WM_repeat)
            tex.set_wrap_v(SamplerState.WM_repeat)
            tex.set_anisotropic_degree(16)
            tex.set_minfilter(SamplerState.FT_linear)
            tex.set_magfilter(SamplerState.FT_linear)

        self._stage.set_shader_input("SpriteTex",  sprite_tex)
        self._stage.set_shader_input("NoiseTex", noise_tex)
