
from panda3d.core import Texture, Vec2

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
        self._jitter_index = 0
        self._compute_jitters()

    @PluginHook("on_stage_setup")
    def setup_stages(self):
        self.debug("Setting up SMAA stages ..")
        self._smaa_stage = self.make_stage(SMAAStage)
        self.register_stage(self._smaa_stage)
        self._load_textures()

    @PluginHook("pre_render_update")
    def update(self):

        # Apply jitter for temporal aa
        jitter = self._jitters[self._jitter_index]
        Globals.base.camLens.set_film_offset(jitter)
        self._smaa_stage.set_jitter_index(self._jitter_index)

        # Sawp jitter index
        self._jitter_index = 1 - self._jitter_index

    def _compute_jitters(self):
        self._jitters = []
        for x, y in ((-0.25,  0.25),(0.25, -0.25)):
            jitter_x = x / float(Globals.base.win.get_x_size()) * 0.5
            jitter_y = y / float(Globals.base.win.get_x_size()) * 0.5
            self._jitters.append((jitter_x, jitter_y))

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

