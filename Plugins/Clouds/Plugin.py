# Load the plugin api
from .. import *

from panda3d.core import Texture, SamplerState 
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
            tex.set_minfilter(Texture.FT_linear)
            tex.set_magfilter(Texture.FT_linear)

        self._stage.set_shader_input("SpriteTex",  sprite_tex)
        self._stage.set_shader_input("NoiseTex", noise_tex)
