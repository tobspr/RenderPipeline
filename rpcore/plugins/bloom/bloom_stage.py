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

from rplibs.six.moves import range

from panda3d.core import Texture, SamplerState, Vec4

from rpcore.globals import Globals
from rpcore.render_stage import RenderStage
from rpcore.image import Image

class BloomStage(RenderStage):

    required_pipes = ["ShadedScene"]
    required_inputs = []

    def __init__(self, pipeline):
        RenderStage.__init__(self, pipeline)
        self.num_mips = 6

    @property
    def produced_pipes(self):
        return {"ShadedScene": self.target_apply.color_tex}

    def create(self):
        self.target_firefly = self.make_target2("RemoveFireflies")
        self.target_firefly.add_color_attachment(bits=16)
        self.target_firefly.prepare_buffer()

        self.scene_target_img = Image.create_2d(
            "BloomDownsample", Globals.base.win.get_x_size(),
            Globals.base.win.get_y_size(), Texture.T_float, Texture.F_r11_g11_b10)

        self.scene_target_img.set_minfilter(SamplerState.FT_linear_mipmap_linear)
        self.scene_target_img.set_magfilter(SamplerState.FT_linear)
        self.scene_target_img.set_wrap_u(SamplerState.WM_clamp)
        self.scene_target_img.set_wrap_v(SamplerState.WM_clamp)
        self.scene_target_img.set_clear_color(Vec4(0.2, 0.6, 1.0, 1.0))
        self.scene_target_img.clear_image()

        self.target_extract = self.make_target2("ExtractBrightSpots")
        self.target_extract.prepare_buffer()
        self.target_extract.set_shader_input("DestTex", self.scene_target_img, False, True, -1, 0)

        self.target_extract.set_shader_input("SourceTex", self.target_firefly.color_tex)

        self.downsample_targets = []
        self.upsample_targets = []

        # Downsample passes
        for i in range(self.num_mips):
            scale_multiplier = 2 ** (1 + i)
            target = self.make_target2("Downsample:Step-" + str(i))
            target.size = -scale_multiplier, -scale_multiplier
            target.prepare_buffer()
            target.set_shader_input("SourceMip", i)
            target.set_shader_input("SourceTex", self.scene_target_img)
            target.set_shader_input("DestTex", self.scene_target_img, False, True, -1, i + 1)
            self.downsample_targets.append(target)

        # Upsample passes
        for i in range(self.num_mips):
            scale_multiplier = 2 ** (self.num_mips - i - 1)
            target = self.make_target2("Upsample:Step-" + str(i))
            target.size = -scale_multiplier, -scale_multiplier
            target.prepare_buffer()
            target.set_shader_input("FirstUpsamplePass", i == 0)

            target.set_shader_input("SourceMip", self.num_mips - i)
            target.set_shader_input("SourceTex", self.scene_target_img)
            target.set_shader_input("DestTex", self.scene_target_img,
                                    False, True, -1, self.num_mips - i - 1)
            self.upsample_targets.append(target)

        self.target_apply = self.make_target2("ApplyBloom")
        self.target_apply.add_color_attachment(bits=16)
        self.target_apply.prepare_buffer()
        self.target_apply.set_shader_input("BloomTex", self.scene_target_img)

    def set_shaders(self):
        self.target_extract.shader = self.load_plugin_shader("extract_bright_spots.frag.glsl")
        self.target_firefly.shader = self.load_plugin_shader("remove_fireflies.frag.glsl")
        self.target_apply.shader = self.load_plugin_shader("apply_bloom.frag.glsl")

        downsample_shader = self.load_plugin_shader("bloom_downsample.frag.glsl")
        for target in self.downsample_targets:
            target.shader = downsample_shader

        upsample_shader = self.load_plugin_shader("bloom_upsample.frag.glsl")
        for target in self.upsample_targets:
            target.shader = upsample_shader
