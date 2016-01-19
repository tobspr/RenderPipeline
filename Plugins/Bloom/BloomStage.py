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

from six.moves import range

from panda3d.core import LVecBase2i, Texture, SamplerState, Vec4
from .. import *

class BloomStage(RenderStage):

    required_pipes = ["ShadedScene"]
    required_inputs = []

    def __init__(self, pipeline):
        RenderStage.__init__(self, "BloomStage", pipeline)
        self._num_mips = 6

    def get_produced_pipes(self):
        return {"ShadedScene": self._upsample_targets[-1]["color"]}

    def set_num_mips(self, mip_count):
        self._num_mips = mip_count

    def create(self):

        self._target_firefly_x = self._create_target("Bloom:RemoveFireflies-X")
        self._target_firefly_x.add_color_texture(bits=16)
        self._target_firefly_x.prepare_offscreen_buffer()

        self._target_firefly_y = self._create_target("Bloom:RemoveFireflies-Y")
        self._target_firefly_y.add_color_texture(bits=16)
        self._target_firefly_y.prepare_offscreen_buffer()

        self._scene_target_img = Image.create_2d(
            "BloomDownsample", Globals.base.win.get_x_size(),
            Globals.base.win.get_y_size(), Texture.T_float, Texture.F_r11_g11_b10)

        self._scene_target_img.set_minfilter(SamplerState.FT_linear_mipmap_linear)
        self._scene_target_img.set_magfilter(SamplerState.FT_linear)
        self._scene_target_img.set_wrap_u(SamplerState.WM_clamp)
        self._scene_target_img.set_wrap_v(SamplerState.WM_clamp)

        self._target_extract = self._create_target("Bloom:ExtractBrightSpots")
        self._target_extract.prepare_offscreen_buffer()
        self._target_extract.set_shader_input("DestTex", self._scene_target_img, False, True, -1, 0)

        self._target_firefly_x.set_shader_input("direction", LVecBase2i(1, 0))
        self._target_firefly_y.set_shader_input("direction", LVecBase2i(0, 1))

        self._target_firefly_y.set_shader_input("SourceTex", self._target_firefly_x["color"])
        self._target_extract.set_shader_input("SourceTex", self._target_firefly_y["color"])

        self._downsample_targets = []
        self._upsample_targets = []

        # Downsample passes
        for i in range(self._num_mips):
            scale_multiplier = 2 ** (1 + i)
            target = self._create_target("Bloom:Downsample:Step-" + str(i))
            target.set_size(-scale_multiplier, -scale_multiplier)
            target.prepare_offscreen_buffer()
            target.set_shader_input("SourceMip", i)
            target.set_shader_input("SourceTex", self._scene_target_img)
            target.set_shader_input("DestTex", self._scene_target_img, False, True, -1, i + 1)
            self._downsample_targets.append(target)

        # Upsample passes
        for i in range(self._num_mips):
            scale_multiplier = 2 ** (self._num_mips - i - 1)
            target = self._create_target("Bloom:Upsample:Step-" + str(i))
            target.set_size(-scale_multiplier, -scale_multiplier)

            if i == self._num_mips - 1:
                target.add_color_texture(bits=16)

            target.prepare_offscreen_buffer()
            target.set_shader_input("FirstUpsamplePass", i == 0)
            target.set_shader_input("LastUpsamplePass", i == self._num_mips - 1)

            target.set_shader_input("SourceMip", self._num_mips - i)
            target.set_shader_input("SourceTex", self._scene_target_img)
            target.set_shader_input("DestTex", self._scene_target_img, False, True, -1, self._num_mips - i - 1)
            self._upsample_targets.append(target)

    def set_shaders(self):
        self._target_extract.set_shader(self._load_plugin_shader("ExtractBrightSpots.frag.glsl"))
        self._target_firefly_x.set_shader(self._load_plugin_shader("RemoveFireflies.frag.glsl"))
        self._target_firefly_y.set_shader(self._load_plugin_shader("RemoveFireflies.frag.glsl"))

        downsample_shader = self._load_plugin_shader("BloomDownsample.frag.glsl")
        upsample_shader = self._load_plugin_shader("BloomUpsample.frag.glsl")
        for target in self._downsample_targets:
            target.set_shader(downsample_shader)  
        for target in self._upsample_targets:
            target.set_shader(upsample_shader)

    def set_shader_input(self, name, handle, *args):
        RenderStage.set_shader_input(self, name, handle, *args) 

        # Special case for the first firefly remove target
        if name == "ShadedScene":
            self._target_firefly_x.set_shader_input("SourceTex", handle)
