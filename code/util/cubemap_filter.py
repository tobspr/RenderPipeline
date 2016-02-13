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

from ..rp_object import RPObject
from .image import Image

class CubemapFilter(RPObject):

    """ Util class for filtering cubemaps, provides funcionality to generate
    a specular and diffuse IBL cubemap. """

    # Fixed size for the diffuse cubemap, since it does not contain much detail
    DIFFUSE_CUBEMAP_SIZE = 10
    PREFILTER_CUBEMAP_SIZE = 32

    def __init__(self, parent_stage, name="Cubemap", size=256):
        """ Inits the filter from a given stage """
        self._stage = parent_stage
        self._name = name
        self._size = size
        self._make_maps()

    def get_specular_cubemap(self):
        """ Returns the generated specular cubemap. The specular cubemap is
        mipmapped and provides the specular IBL components of the input cubemap. """
        return self._specular_map

    specular_cubemap = property(get_specular_cubemap)

    def get_diffuse_cubemap(self):
        """ Returns the generated diffuse cubemap. The diffuse cubemap has no
        mipmaps and contains the filtered diffuse component of the input cubemap. """
        return self._diffuse_map

    diffuse_cubemap = property(get_diffuse_cubemap)

    def get_target_cubemap(self):
        """ Returns the target where the caller should write the initial cubemap
        data to """
        return self._specular_map

    target_cubemap = property(get_target_cubemap)

    def get_size(self):
        """ Returns the size of the created cubemap, previously passed to the
        constructor of the filter """
        return self._size

    size = property(get_size)

    def create(self):
        """ Creates the filter. The input cubemap should be mipmapped, and will
        get reused for the specular cubemap. """
        self._make_specular_targets()
        self._make_diffuse_target()

    def _make_maps(self):
        """ Internal method to create the cubemap storage """

        # Create the cubemaps for the diffuse and specular components
        self._prefilter_map = Image.create_cube(
            self._name + "IBLPrefDiff", CubemapFilter.PREFILTER_CUBEMAP_SIZE,
            Texture.T_float, Texture.F_r11_g11_b10)
        self._diffuse_map = Image.create_cube(
            self._name + "IBLDiff", CubemapFilter.DIFFUSE_CUBEMAP_SIZE,
            Texture.T_float, Texture.F_r11_g11_b10)
        self._spec_pref_map = Image.create_cube(
            self._name + "IBLPrefSpec", self._size, Texture.T_float, Texture.F_r11_g11_b10)
        self._specular_map = Image.create_cube(
            self._name + "IBLSpec", self._size, Texture.T_float, Texture.F_r11_g11_b10)

        # Set the correct filtering modes
        for tex in [self._diffuse_map, self._specular_map, self._prefilter_map]:
            tex.set_minfilter(SamplerState.FT_linear)
            tex.set_magfilter(SamplerState.FT_linear)

        # Use mipmaps for the specular cubemap
        self._spec_pref_map.set_minfilter(SamplerState.FT_linear_mipmap_linear)
        self._specular_map.set_minfilter(SamplerState.FT_linear_mipmap_linear)

    def _make_specular_targets(self):
        """ Internal method to create the specular mip chain """
        self._targets_spec = []
        self._targets_spec_filter = []
        mip, mipsize = 0, self._size
        while mipsize >= 2:

            # Assuming an initial size of a power of 2, its safe to do this
            mipsize = mipsize // 2

            # Create the target which downsamples the mipmap
            target = self._stage.make_target(
                self._name + "SpecIBL-" + str(mipsize))
            target.size = mipsize * 6, mipsize
            target.prepare_offscreen_buffer()

            if mip == 0:
                target.set_shader_input("SourceTex", self._specular_map)
            else:
                target.set_shader_input("SourceTex", self._spec_pref_map)
            target.set_shader_input(
                "DestMipmap", self._spec_pref_map, False, True, -1,
                mip + 1, 0)
            target.set_shader_input("currentMip", mip)

            mip += 1

            # Create the target which filters the mipmap and removes the noise
            target_filter = self._stage.make_target(
                self._name + "SpecIBLFilter-" + str(mipsize))
            target_filter.size = mipsize * 6, mipsize
            target_filter.prepare_offscreen_buffer()
            target_filter.set_shader_input("currentMip", mip)
            target_filter.set_shader_input("SourceTex", self._spec_pref_map)
            target_filter.set_shader_input(
                "DestMipmap", self._specular_map, False, True, -1, mip, 0)

            self._targets_spec.append(target)
            self._targets_spec_filter.append(target_filter)

    def _make_diffuse_target(self):
        """ Internal method to create the diffuse cubemap """

        # Create the target which integrates the lambert brdf
        self._diffuse_target = self._stage.make_target(self._name + "DiffuseIBL")
        self._diffuse_target.size = (CubemapFilter.PREFILTER_CUBEMAP_SIZE * 6,
            CubemapFilter.PREFILTER_CUBEMAP_SIZE)
        self._diffuse_target.prepare_offscreen_buffer()

        self._diffuse_target.set_shader_input("SourceCubemap", self._specular_map)
        self._diffuse_target.set_shader_input("DestCubemap", self._prefilter_map)
        self._diffuse_target.set_shader_input("cubeSize", CubemapFilter.PREFILTER_CUBEMAP_SIZE)

        # Create the target which removes the noise from the previous target,
        # which is introduced with importance sampling
        self._diff_filter_target = self._stage.make_target(self._name + "DiffPrefIBL")
        self._diff_filter_target.size = (CubemapFilter.DIFFUSE_CUBEMAP_SIZE * 6,
            CubemapFilter.DIFFUSE_CUBEMAP_SIZE)
        self._diff_filter_target.prepare_offscreen_buffer()

        self._diff_filter_target.set_shader_input("SourceCubemap", self._prefilter_map)
        self._diff_filter_target.set_shader_input("DestCubemap", self._diffuse_map)
        self._diff_filter_target.set_shader_input("cubeSize", CubemapFilter.DIFFUSE_CUBEMAP_SIZE)

    def set_shaders(self):
        """ Sets all required shaders on the filter. """
        self._diffuse_target.set_shader(
            self._stage.load_shader("stages/ibl_cubemap_diffuse.frag.glsl"))
        self._diff_filter_target.set_shader(
            self._stage.load_shader("stages/ibl_cubemap_diffuse_filter.frag.glsl"))
        mip_shader = self._stage.load_shader("stages/ibl_cubemap_specular.frag.glsl")
        for target in self._targets_spec:
            target.set_shader(mip_shader)
        mip_filter_shader = self._stage.load_shader(
            "stages/ibl_cubemap_specular_filter.frag.glsl")
        for target in self._targets_spec_filter:
            target.set_shader(mip_filter_shader)
