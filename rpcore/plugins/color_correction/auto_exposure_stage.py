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

from ...render_stage import RenderStage
from panda3d.core import Texture, Vec4

class AutoExposureStage(RenderStage):

    required_pipes = ["ShadedScene"]
    required_inputs = []

    def __init__(self, pipeline):
        RenderStage.__init__(self, "AutoExposureStage", pipeline)

    @property
    def produced_pipes(self):
        return {"ShadedScene": self._target_apply["color"],
                "Exposure": self._tex_exposure}

    def create(self):

        # Create the target which converts the scene color to a luminance
        self._target_lum = self.make_target("GetLuminance")
        self._target_lum.set_quarter_resolution()
        self._target_lum.add_color_texture(bits=(16, 0, 0, 0))
        self._target_lum.prepare_offscreen_buffer()

        # Get the current quarter-window size
        wsize_x = (Globals.base.win.get_x_size() + 3) // 4
        wsize_y = (Globals.base.win.get_y_size() + 3) // 4

        # Create the targets which downscale the luminance mipmaps
        self._mip_targets = []
        last_tex = self._target_lum["color"]
        while wsize_x >= 4 or wsize_y >= 4:
            wsize_x = (wsize_x+3) // 4
            wsize_y = (wsize_y+3) // 4

            mip_target = self.make_target("DScaleLum:S" + str(wsize_x))
            mip_target.add_color_texture(bits=(16, 0, 0, 0))
            mip_target.size = wsize_x, wsize_y
            mip_target.prepare_offscreen_buffer()
            mip_target.set_shader_input("SourceTex", last_tex)
            self._mip_targets.append(mip_target)
            last_tex = mip_target["color"]

        # Create the storage for the exposure, this stores the current and last
        # frames exposure
        self._tex_exposure = Image.create_buffer(
            "ExposureStorage", 1, Texture.T_float, Texture.F_rgba16)
        self._tex_exposure.set_clear_color(Vec4(0.5))
        self._tex_exposure.clear_image()

        # Create the target which extracts the exposure from the average brightness
        self._target_analyze = self.make_target("AnalyzeBrightness")
        self._target_analyze.size = 1, 1
        self._target_analyze.prepare_offscreen_buffer()

        self._target_analyze.set_shader_input(
            "ExposureStorage", self._tex_exposure)
        self._target_analyze.set_shader_input("DownscaledTex", last_tex)

        # Create the target which applies the generated exposure to the scene
        self._target_apply = self.make_target("ApplyExposure")
        self._target_apply.add_color_texture(bits=16)
        self._target_apply.prepare_offscreen_buffer()
        self._target_apply.set_shader_input("Exposure", self._tex_exposure)

    def set_shaders(self):
        self._target_lum.set_shader(self.load_plugin_shader("generate_luminance.frag.glsl"))
        self._target_analyze.set_shader(self.load_plugin_shader("analyze_brightness.frag.glsl"))
        self._target_apply.set_shader(self.load_plugin_shader("apply_exposure.frag.glsl"))

        mip_shader = self.load_plugin_shader("downscale_luminance.frag.glsl")
        for target in self._mip_targets:
            target.set_shader(mip_shader)
