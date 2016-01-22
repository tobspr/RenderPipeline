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

from panda3d.core import Camera, NodePath, SamplerState

from ..RenderStage import RenderStage
from ..Globals import Globals

class ShadowStage(RenderStage):

    """ This is the stage which renders all shadows """
    required_inputs = []

    def __init__(self, pipeline):
        RenderStage.__init__(self, "ShadowStage", pipeline)
        self._size = 4096

    def set_size(self, size):
        self._size = size

    def get_produced_pipes(self):
        return {
            "ShadowAtlas": self._target["depth"],
            "ShadowAtlasPCF": (self._target['depth'], self.make_pcf_state()),
        }

    def make_pcf_state(self):
        state = SamplerState()
        state.set_minfilter(SamplerState.FT_shadow)
        state.set_magfilter(SamplerState.FT_shadow)
        return state

    def create(self):
        self._target = self._create_target("ShadowAtlas")
        self._target.set_source(source_cam=NodePath(Camera("dummy_shadow_cam")), source_win=Globals.base.win)
        self._target.size = self._size, self._size
        self._target.create_overlay_quad = False
        self._target.add_depth_texture(bits=32)
        self._target.prepare_scene_render()

        # Disable all clears
        self._target.get_internal_region().disable_clears()
        self._target.get_internal_buffer().disable_clears()

        self._target.set_clear_depth(False)



    def set_shader_input(self, *args):
        Globals.render.set_shader_input(*args)
