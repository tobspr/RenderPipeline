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

from panda3d.core import SamplerState, Texture, Vec4

from rpcore.render_stage import RenderStage
from rpcore.image import Image

class CloudStage(RenderStage):

    """ This stage handles the volumetric cloud rendering """

    required_pipes = ["ShadedScene", "GBuffer", "ScatteringIBLDiffuse"]

    def __init__(self, pipeline):
        RenderStage.__init__(self, "CloudStage", pipeline)
        self._voxel_res_xy = 256
        self._voxel_res_z = 32

    @property
    def produced_pipes(self):
        return {"ShadedScene": self._target_apply_clouds["color"]}

    @property
    def produced_defines(self):
        return {
            "CLOUD_RES_XY": self._voxel_res_xy,
            "CLOUD_RES_Z": self._voxel_res_z
        }

    def create(self):
        # Construct the voxel texture
        self._cloud_voxels = Image.create_3d(
            "CloudVoxels", self._voxel_res_xy, self._voxel_res_xy, self._voxel_res_z,
            Texture.T_unsigned_byte, Texture.F_rgba8)
        self._cloud_voxels.set_wrap_u(SamplerState.WM_repeat)
        self._cloud_voxels.set_wrap_v(SamplerState.WM_repeat)
        self._cloud_voxels.set_wrap_w(SamplerState.WM_border_color)
        self._cloud_voxels.set_border_color(Vec4(0, 0, 0, 0))

        # Construct the target which populates the voxel texture
        self._grid_target = self.make_target("CreateVoxels")
        self._grid_target.size = self._voxel_res_xy, self._voxel_res_xy
        self._grid_target.prepare_offscreen_buffer()
        self._grid_target.quad.set_instance_count(self._voxel_res_z)
        self._grid_target.set_shader_input("CloudVoxels", self._cloud_voxels)

        # Construct the target which shades the voxels
        self._shade_target = self.make_target("ShadeVoxels")
        self._shade_target.size = self._voxel_res_xy, self._voxel_res_xy
        self._shade_target.prepare_offscreen_buffer()
        self._shade_target.quad.set_instance_count(self._voxel_res_z)
        self._shade_target.set_shader_input("CloudVoxels", self._cloud_voxels)
        self._shade_target.set_shader_input("CloudVoxelsDest", self._cloud_voxels)

        self._render_target = self.make_target("RaymarchVoxels")
        self._render_target.set_half_resolution()
        self._render_target.has_color_alpha = True
        self._render_target.add_color_texture(bits=16)
        self._render_target.prepare_offscreen_buffer()
        self._render_target.set_shader_input("CloudVoxels", self._cloud_voxels)

        self._target_apply_clouds = self.make_target("MergeWithScene")
        self._target_apply_clouds.add_color_texture(bits=16)
        self._target_apply_clouds.prepare_offscreen_buffer()

        self._target_apply_clouds.set_shader_input(
            "CloudsTex", self._render_target["color"])

    def set_shaders(self):
        self._grid_target.set_shader(
            self.load_plugin_shader(
                "$$shader/default_post_process_instanced.vert.glsl",
                "generate_clouds.frag.glsl"))
        self._target_apply_clouds.set_shader(
            self.load_plugin_shader("apply_clouds.frag.glsl"))
        self._shade_target.set_shader(
            self.load_plugin_shader(
                "$$shader/default_post_process_instanced.vert.glsl",
                "shade_clouds.frag.glsl"))
        self._render_target.set_shader(
            self.load_plugin_shader("render_clouds.frag.glsl"))
