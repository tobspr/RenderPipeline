
from __future__ import division

from panda3d.core import Texture

from ..RenderStage import RenderStage
from ..Globals import Globals
from ..Util.Image import Image

class DownscaleZStage(RenderStage):

    """ This stage downscales the z buffer """

    required_pipes = ["GBuffer"] 

    def __init__(self, pipeline):
        RenderStage.__init__(self, "DownscaleZStage", pipeline)

    def get_produced_pipes(self):
        return {"DownscaledDepth": self._depth_storage.get_texture()}

    def create(self):

        res = Globals.resolution
        current_dim = max(res.x, res.y)
        current_res = res.x, res.y

        self._depth_storage = Image.create_2d("DownscaledZ", res.x, res.y, Texture.T_float, Texture.F_rg32)
        self._depth_storage.get_texture().set_minfilter(Texture.FT_nearest_mipmap_nearest)
        self._depth_storage.get_texture().set_magfilter(Texture.FT_nearest)
        self._depth_storage.get_texture().set_wrap_u(Texture.WM_clamp)
        self._depth_storage.get_texture().set_wrap_v(Texture.WM_clamp)

        self._target_copy = self._create_target("CopyZBuffer")
        self._target_copy.prepare_offscreen_buffer()
        self._target_copy.set_shader_input("DestTexture", self._depth_storage.get_texture())

        self._mip_targets = []

        mip = 0
        while current_dim >= 1:
            current_dim = current_dim // 2
            current_res = (current_res[0] + 1) // 2, (current_res[1] + 1) // 2

            target = self._create_target("DownscaleZ-" + str(mip))
            target.set_size(*current_res)
            target.prepare_offscreen_buffer()
            target.set_shader_input("SourceImage", self._depth_storage.get_texture(), True, False, -1, mip, 0)
            target.set_shader_input("DestImage", self._depth_storage.get_texture(), False, True, -1, mip + 1, 0)

            mip += 1
            self._mip_targets.append(target)

    def set_shaders(self):
        mip_shader = self._load_shader("Stages/DownscaleZBuffer.frag")
        for target in self._mip_targets:
            target.set_shader(mip_shader)
        self._target_copy.set_shader(self._load_shader("Stages/CopyZBuffer.frag"))

    def resize(self):
        RenderStage.resize(self)
        self.debug("Resizing pass")

    def cleanup(self):
        RenderStage.cleanup(self)
        self.debug("Cleanup pass")
