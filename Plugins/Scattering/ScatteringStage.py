
from __future__ import division

from .. import *

from panda3d.core import Texture


class ScatteringStage(RenderStage):

    """ This stage uses the precomputed data to display the scattering """

    required_pipes = ["ShadedScene", "GBuffer"]
    required_inputs = ["mainCam", "mainRender", "cameraPosition", "DefaultSkydome",
                       "DefaultEnvmap", "TimeOfDay"]

    def __init__(self, pipeline):
        RenderStage.__init__(self, "ScatteringStage", pipeline)

    def get_produced_pipes(self):
        return {
            "ShadedScene": self._target['color'],
            "ScatteringCubemap": self._scatter_cubemap.get_texture()
        }

    def create(self):


        self._target = self._create_target("ScatteringStage")
        self._target.add_color_texture(bits=16)
        self._target.prepare_offscreen_buffer()

        cubemap_size = 256

        self._scatter_cubemap = Image.create_cube("ScatteringCubemap", cubemap_size, Texture.T_float, Texture.F_rgba16)
        self._scatter_cubemap.get_texture().set_minfilter(Texture.FT_linear_mipmap_linear)
        self._scatter_cubemap.get_texture().set_magfilter(Texture.FT_linear)

        self._target_cube = self._create_target("ScatteringCubemap")
        # self._target_cube.add_color_texture()
        self._target_cube.set_size(cubemap_size * 6, cubemap_size)
        self._target_cube.prepare_offscreen_buffer()
        self._target_cube.set_shader_input("DestCubemap", self._scatter_cubemap.get_texture())

        # Create the mipmaps for the cubemap manually, since we need to
        # filter it in order to make it look smooth
        mipsize = cubemap_size
        mip = 0
        self._mip_targets = []
        while mipsize >= 2:
            mipsize = mipsize // 2
            target = self._create_target("DownscaleScatterCubemap-" + str(mipsize))
            target.set_size(mipsize * 6, mipsize)
            # target.add_color_texture()
            target.prepare_offscreen_buffer()
            target.set_shader_input("SourceMipmap", self._scatter_cubemap.get_texture())
            target.set_shader_input("DestMipmap", self._scatter_cubemap.get_texture(), False, True, -1, mip + 1, 0)
            target.set_shader_input("current_mip", mip)
            mip += 1

            self._mip_targets.append(target)

        # Make the ambient stage use our cubemap
        get_internal_stage_handle(AmbientStage).add_pipe_requirement("ScatteringCubemap")

    def set_shaders(self):
        self._target.set_shader(
            self.load_plugin_shader("ApplyScattering.frag.glsl"))
        self._target_cube.set_shader(
            self.load_plugin_shader("ScatteringEnvmap.frag.glsl"))

        mip_shader = self.load_plugin_shader("DownsampleEnvmap.frag.glsl") 
        for target in self._mip_targets:
            target.set_shader(mip_shader)

    def resize(self):
        RenderStage.resize(self)
        self.debug("Resizing pass")

    def cleanup(self):
        RenderStage.cleanup(self)
        self.debug("Cleanup pass")
