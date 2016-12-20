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

from panda3d.core import SamplerState

from rpcore.loader import RPLoader
from rpcore.pluginbase.base_plugin import BasePlugin

from .smaa_stage import SMAAStage

class Plugin(BasePlugin):

    name = "SMAA (Antialiasing)"
    author = "tobspr <tobias.springer1@gmail.com>"
    description = ("This plugin adds support for SMAA, a post process "
                   "antialiasing technique.")
    version = "1.5"

    def on_stage_setup(self):
        self._smaa_stage = self.create_stage(SMAAStage)
        self._load_textures()

    def _load_textures(self):
        """ Loads all required textures """
        search_tex = RPLoader.load_texture(self.get_resource("search_tex.png"))
        area_tex = RPLoader.load_texture(self.get_resource("area_tex.png"))

        for tex in [search_tex, area_tex]:
            tex.set_minfilter(SamplerState.FT_linear)
            tex.set_magfilter(SamplerState.FT_linear)
            tex.set_wrap_u(SamplerState.WM_clamp)
            tex.set_wrap_v(SamplerState.WM_clamp)

        self._smaa_stage.area_tex = area_tex
        self._smaa_stage.search_tex = search_tex
