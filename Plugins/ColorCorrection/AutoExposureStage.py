
from __future__ import division

from .. import *
from panda3d.core import Texture, Vec4

class AutoExposureStage(RenderStage):

    required_pipes = ["ShadedScene"]
    required_inputs = []

    def __init__(self, pipeline):
        RenderStage.__init__(self, "AutoExposureStage", pipeline)

    def get_produced_pipes(self):
        return {"ShadedScene": self._target_apply["color"],
                "Exposure": self._tex_exposure.get_texture()}

    def create(self):

        # Create the target which converts the scene color to a luminance
        self._target_lum = self._create_target("ColorCorrection:GetLuminance")
        self._target_lum.set_quarter_resolution()
        self._target_lum.add_color_texture(bits=16)
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

            mip_target = self._create_target("ColorCorrection:DScaleLum:S" + str(wsize_x))
            mip_target.add_color_texture(bits=16)
            mip_target.set_size(wsize_x, wsize_y)
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
        self._target_analyze = self._create_target("ColorCorrection:AnalyzeBrightness")
        self._target_analyze.set_size(1, 1)
        self._target_analyze.prepare_offscreen_buffer()

        self._target_analyze.set_shader_input(
            "ExposureStorage", self._tex_exposure.get_texture())
        self._target_analyze.set_shader_input("DownscaledTex", last_tex)

        # Create the target which applies the generated exposure to the scene
        self._target_apply = self._create_target("ColorCorrection:ApplyExposure")
        self._target_apply.add_color_texture(bits=16)
        self._target_apply.prepare_offscreen_buffer()
        self._target_apply.set_shader_input("Exposure", self._tex_exposure.get_texture())

    def set_shaders(self):
        self._target_lum.set_shader(self.load_plugin_shader("GenerateLuminance.frag.glsl"))
        self._target_analyze.set_shader(self.load_plugin_shader("AnalyzeBrightness.frag.glsl"))
        self._target_apply.set_shader(self.load_plugin_shader("ApplyExposure.frag.glsl"))

        mip_shader = self.load_plugin_shader("DownscaleLuminance.frag.glsl")
        for target in self._mip_targets:
            target.set_shader(mip_shader)

    def resize(self):
        RenderStage.resize(self)
        self.debug("Resizing pass")

    def cleanup(self):
        RenderStage.cleanup(self)
        self.debug("Cleanup pass")
