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

from .. import *

from panda3d.core import Texture


class ScatteringStage(RenderStage):

    """ This stage uses the precomputed data to display the scattering """

    required_pipes = ["ShadedScene", "GBuffer"]
    required_inputs = ["DefaultSkydome", "DefaultEnvmap"]

    def __init__(self, pipeline):
        RenderStage.__init__(self, "ScatteringStage", pipeline)

    def get_produced_pipes(self):
        return {
            "ShadedScene": self._target['color'],
            "ScatteringCubemap": self._scatter_cubemap.get_texture()
        }

    def create(self):

        self._target = self._create_target("Scattering:SkyboxScattering")
        self._target.add_color_texture(bits=16)
        self._target.prepare_offscreen_buffer()

        cubemap_size = 256

        self._scatter_cubemap = Image.create_cube(
            "ScatteringCubemap", cubemap_size, Texture.T_float, Texture.F_r11_g11_b10)
        self._scatter_cubemap.get_texture().set_minfilter(Texture.FT_linear_mipmap_linear)
        self._scatter_cubemap.get_texture().set_magfilter(Texture.FT_linear)

        self._target_cube = self._create_target("Scattering:EnvironmentCubemap")
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
            target = self._create_target("Scattering:DownscaleCubemap:Mip-" + str(mipsize))
            target.set_size(mipsize * 6, mipsize)
            # target.add_color_texture()
            target.prepare_offscreen_buffer()
            target.set_shader_input(
                "SourceTex", self._scatter_cubemap.get_texture())
            target.set_shader_input(
                "DestMipmap", self._scatter_cubemap.get_texture(), False, True, -1, mip + 1, 0)
            target.set_shader_input("current_mip", mip)
            mip += 1

            self._mip_targets.append(target)

        # Make the ambient stage use our cubemap
        get_internal_stage("AmbientStage").add_pipe_requirement("ScatteringCubemap")

    def set_shaders(self):
        self._target.set_shader(
            self._load_plugin_shader("ApplyScattering.frag.glsl"))
        self._target_cube.set_shader(
            self._load_plugin_shader("ScatteringEnvmap.frag.glsl"))

        mip_shader = self._load_plugin_shader("DownsampleEnvmap.frag.glsl")
        for target in self._mip_targets:
            target.set_shader(mip_shader)

    def resize(self):
        RenderStage.resize(self)
        self.debug("Resizing pass")

    def cleanup(self):
        RenderStage.cleanup(self)
        self.debug("Cleanup pass")
