
from panda3d.core import Texture

# Load plugin api
from .. import *


from SMAAStage import SMAAStage

# Create the main plugin
class Plugin(BasePlugin):

    NAME = "SMAA"
    DESCRIPTION = """ This plugin adds support for SMAA T2 """
    SETTINGS = {}

    def __init__(self, pipeline):
        BasePlugin.__init__(self, pipeline)

    @PluginHook("on_stage_setup")
    def setup_stages(self):
        self.debug("Setting up SMAA stages ..")
        self._smaa_stage = self.make_stage(SMAAStage)
        self.register_stage(self._smaa_stage)
        self._load_textures()

    def _load_textures(self):
        self.debug("Loading SMAA textures ..")
        self.search_tex = Globals.loader.loadTexture(self.get_resource("SearchTex.png"))
        self.area_tex = Globals.loader.loadTexture(self.get_resource("AreaTex.png"))

        for tex in [self.search_tex, self.area_tex]:
            tex.set_minfilter(Texture.FT_linear)
            tex.set_magfilter(Texture.FT_linear)
            tex.set_wrap_u(Texture.WM_clamp)
            tex.set_wrap_v(Texture.WM_clamp)

        self._smaa_stage.set_area_tex(self.area_tex)
        self._smaa_stage.set_search_tex(self.search_tex)
