"""

RenderPipeline

Copyright (c) 2014-2015 tobspr <tobias.springer1@gmail.com>

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

from panda3d.core import SamplerState

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
        for x, y in ((-0.25, 0.25), (0.25, -0.25)):

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
            tex.set_minfilter(SamplerState.FT_linear)
            tex.set_magfilter(SamplerState.FT_linear)
            tex.set_wrap_u(SamplerState.WM_clamp)
            tex.set_wrap_v(SamplerState.WM_clamp)

        self._smaa_stage.set_area_tex(self._area_tex)
        self._smaa_stage.set_search_tex(self._search_tex)

