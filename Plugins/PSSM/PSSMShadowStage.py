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
from __future__ import division
from six.moves import range

from .. import *
from panda3d.core import SamplerState, Texture

class PSSMShadowStage(RenderStage):

    """ This stage generates the depth-maps used for rendering PSSM """

    required_inputs = []

    def __init__(self, pipeline):
        RenderStage.__init__(self, "PSSMShadowStage", pipeline)
        self._num_splits = 3
        self._split_resolution = 512
        self._split_regions = []

    def get_produced_pipes(self):
        return {
            "PSSMShadowAtlas": self._target['depth'],
            "PSSMShadowAtlasPCF": (self._target['depth'], self.make_pcf_state()),
        }

    def make_pcf_state(self):
        state = SamplerState()
        state.set_minfilter(Texture.FT_shadow)
        state.set_magfilter(Texture.FT_shadow)
        return state

    def set_num_splits(self, splits):
        self._num_splits = splits

    def set_split_resolution(self, res):
        self._split_resolution = res

    def get_split_region(self, index):
        return self._split_regions[index]

    def get_shadow_tex(self):
        return self._target["depth"]

    def create(self):
        self._target = self._create_target("PSSMShadowMap")
        self._target.set_source(None, Globals.base.win)
        self._target.set_size(self._split_resolution * self._num_splits, self._split_resolution)
        self._target.add_depth_texture(bits=32)
        self._target.set_create_overlay_quad(False)
        self._target.set_color_write(False)
        self._target.prepare_scene_render()

        # Remove all unused display regions
        internal_buffer = self._target.get_internal_buffer()
        internal_buffer.remove_all_display_regions()
        internal_buffer.get_display_region(0).set_active(False)

        # Prepare the display regions
        for i in range(self._num_splits):
            region = internal_buffer.make_display_region(
                i / self._num_splits,
                i / self._num_splits + 1 / self._num_splits, 0, 1)
            region.set_clear_depth(1)
            region.set_clear_color_active(False)
            region.set_clear_depth_active(True)
            region.set_sort(25 + i)
            region.set_active(True)
            self._split_regions.append(region)

    def set_shader_input(self, *args):
        Globals.render.set_shader_input(*args)

    def resize(self):
        RenderStage.resize(self)
        self.debug("Resizing pass")

    def cleanup(self):
        RenderStage.cleanup(self)
        self.debug("Cleanup pass")
