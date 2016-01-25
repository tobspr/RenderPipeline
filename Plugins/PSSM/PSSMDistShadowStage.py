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
from __future__ import division
from six.moves import range

from .. import *
from panda3d.core import SamplerState

class PSSMDistShadowStage(RenderStage):

    """ This stage generates a depth map using Variance Shadow Maps for very
    distant objects. """

    required_inputs = []

    def __init__(self, pipeline):
        RenderStage.__init__(self, "PSSMDistShadowStage", pipeline)
        self._resolution = 4096

    def get_produced_pipes(self):
        return {
            "PSSMVSMShadowMap": self._target['depth'],
        }

    def set_resolution(self, res):
        self._resolution = res

    def create(self):
        self._target = self.make_target("PSSMDistShadowMap")
        self._target.set_source(None, Globals.base.win)
        self._target.size = self._resolution
        self._target.add_depth_texture(bits=32)
        self._target.create_overlay_quad = False
        self._target.color_write = False
        self._target.prepare_scene_render()

    def set_shader_input(self, *args):
        Globals.render.set_shader_input(*args)
