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

from .. import *
from panda3d.core import SamplerState

class VXGIStage(RenderStage):

    required_inputs = ["voxelGridPosition", "Noise4x4"]
    required_pipes = ["ShadedScene", "SceneVoxels", "GBuffer", "ScatteringIBLSpecular",
                      "ScatteringIBLDiffuse"]

    def __init__(self, pipeline):
        RenderStage.__init__(self, "VXGIStage", pipeline)

    def get_produced_pipes(self):
        return {
            "VXGISpecular": self._target_spec["color"],
            "VXGIDiffuse": self._target_upscale_diff["color"]
        }

    def create(self):

        # Create a target for the specular GI
        self._target_spec = self._create_target("VXGI:SpecularGI")
        self._target_spec.add_color_texture(bits=16)
        self._target_spec.prepare_offscreen_buffer()

        # Create a target for the diffuse GI
        self._target_diff = self._create_target("VXGI:DiffuseGI")
        self._target_diff.set_half_resolution()
        self._target_diff.add_color_texture(bits=16)
        self._target_diff.prepare_offscreen_buffer()
        self._target_diff.quad.set_instance_count(4)

        # Create the target which de-interleaves the diffuse target
        self._target_merge_diff = self._create_target("VXGI:MergeDiffuseGI")
        self._target_merge_diff.set_half_resolution()
        self._target_merge_diff.add_color_texture(bits=16)
        self._target_merge_diff.prepare_offscreen_buffer()
        self._target_merge_diff.set_shader_input("SourceTex", self._target_diff["color"])

       # Create the target which bilateral upsamples the diffuse target
        self._target_upscale_diff = self._create_target("VXGI:UpscaleDiffuse")
        self._target_upscale_diff.add_color_texture(bits=16)
        self._target_upscale_diff.prepare_offscreen_buffer()
        self._target_upscale_diff.set_shader_input("SourceTex", self._target_merge_diff["color"])

        # Make the ambient stage use the GI result
        ambient_stage = get_internal_stage("AmbientStage")
        ambient_stage.add_pipe_requirement("VXGISpecular")
        ambient_stage.add_pipe_requirement("VXGIDiffuse")

    def set_shaders(self):
        self._target_spec.set_shader(
            self._load_plugin_shader("VXGISpecular.frag"))
        self._target_diff.set_shader(
            self._load_plugin_shader("Shader/SampleHalfresInterleaved.vert", "VXGIDiffuse.frag"))
        self._target_merge_diff.set_shader(
            self._load_plugin_shader("Shader/MergeInterleavedTarget.frag"))
        self._target_upscale_diff.set_shader(
            self._load_plugin_shader("Shader/BilateralUpscale.frag"))
