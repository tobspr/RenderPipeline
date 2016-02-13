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

from panda3d.core import Texture, SamplerState

from ..RenderStage import RenderStage
from ..Globals import Globals
from ..Util.Image import Image

class DownscaleZStage(RenderStage):

    """ This stage downscales the z buffer """

    required_pipes = ["GBuffer"]

    def __init__(self, pipeline):
        RenderStage.__init__(self, "DownscaleZStage", pipeline)

    @property
    def produced_pipes(self):
        return {"DownscaledDepth": self._depth_storage}

    def create(self):

        res = Globals.resolution
        current_dim = max(res.x, res.y)
        current_res = res.x, res.y

        self._depth_storage = Image.create_2d(
            "DownscaledZ", res.x, res.y, Texture.T_float, Texture.F_rg32)
        self._depth_storage.set_minfilter(SamplerState.FT_nearest_mipmap_nearest)
        self._depth_storage.set_magfilter(SamplerState.FT_nearest)
        self._depth_storage.set_wrap_u(SamplerState.WM_clamp)
        self._depth_storage.set_wrap_v(SamplerState.WM_clamp)

        self._target_copy = self.make_target("CopyZBuffer")
        self._target_copy.prepare_offscreen_buffer()
        self._target_copy.set_shader_input("DestTexture", self._depth_storage)

        self._mip_targets = []

        mip = 0
        while current_dim >= 1:
            current_dim = current_dim // 2
            current_res = (current_res[0] + 1) // 2, (current_res[1] + 1) // 2

            target = self.make_target("DownscaleZ-" + str(mip))
            target.size = current_res
            target.prepare_offscreen_buffer()
            target.set_shader_input(
                "SourceImage", self._depth_storage)
            target.set_shader_input(
                "DestImage", self._depth_storage, False, True, -1, mip + 1, 0)
            target.set_shader_input("CurrentLod", mip)

            mip += 1
            self._mip_targets.append(target)

    def set_shaders(self):
        mip_shader = self.load_shader("Stages/DownscaleZBuffer.frag")
        for target in self._mip_targets:
            target.set_shader(mip_shader)
        self._target_copy.set_shader(self.load_shader("Stages/CopyZBuffer.frag"))
