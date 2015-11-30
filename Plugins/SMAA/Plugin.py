
from panda3d.core import Texture, Vec2

# Load plugin api
from .. import *

from .SMAAStage import SMAAStage

# Create the main plugin
class Plugin(BasePlugin):

    @PluginHook("on_stage_setup")
    def setup_stages(self):
        self.debug("Setting up SMAA stages ..")

        if self.get_setting("use_reprojection"):
            self._jitter_index = 0
            self._compute_jitters()

        self._smaa_stage = self.create_stage(SMAAStage)
        self._smaa_stage.set_use_reprojection(self.get_setting("use_reprojection"))
        self._load_textures()

    @PluginHook("pre_render_update")
    def update(self):

        # Apply jitter for temporal aa
        if self.get_setting("use_reprojection"):
            jitter = self._jitters[self._jitter_index]
            Globals.base.camLens.set_film_offset(jitter)
            self._smaa_stage.set_jitter_index(self._jitter_index)

            # Sawp jitter index
            self._jitter_index = 1 - self._jitter_index


    def _compute_jitters(self):
        self._jitters = []
        for x, y in ((-0.25,  0.25),(0.25, -0.25)):
            
            # The get_x_size() for both dimensions is not an error! Its due to
            # how the OrtographicLens works internally.
            jitter_x = x / float(Globals.base.win.get_x_size())
            jitter_y = y / float(Globals.base.win.get_x_size())
            self._jitters.append((jitter_x, jitter_y))

    def _load_textures(self):
        self.debug("Loading SMAA textures ..")
        self._search_tex = Globals.loader.loadTexture(self.get_resource("SearchTex.png"))
        self._area_tex = Globals.loader.loadTexture(self.get_resource("AreaTex.png"))

        for tex in [self._search_tex, self._area_tex]:
            tex.set_minfilter(Texture.FT_linear)
            tex.set_magfilter(Texture.FT_linear)
            tex.set_wrap_u(Texture.WM_clamp)
            tex.set_wrap_v(Texture.WM_clamp)

        self._smaa_stage.set_area_tex(self._area_tex)
        self._smaa_stage.set_search_tex(self._search_tex)

