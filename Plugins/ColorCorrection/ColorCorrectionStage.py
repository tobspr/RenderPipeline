
from __future__ import division

from .. import *
from panda3d.core import Texture, Vec4

class ColorCorrectionStage(RenderStage):

    required_inputs = ["PrecomputedGrain"]
    required_pipes = ["ShadedScene"]

    def __init__(self, pipeline):
        RenderStage.__init__(self, "ColorCorrectionStage", pipeline)
        self._use_sharpen = False

    def set_use_sharpen(self, flag):
        self._use_sharpen = flag

    def create(self):
        self._target = self._create_target("ColorCorrectionStage")

        # Create the sharpen target
        if self._use_sharpen:

            # When using a sharpen filter, the main target needs a color texture
            self._target.add_color_texture(bits=8)
            self._target.prepare_offscreen_buffer()

            self._target_sharpen = self._create_target("SharpenFilter")
            # We don't have a color attachment, but still want to write color
            self._target_sharpen.set_color_write(True)
            self._target_sharpen.prepare_offscreen_buffer()
            self._target_sharpen.make_main_target()

            # Use a linear filter for the color texture, this is required for the sharpen
            # filter to work properly.
            self._target["color"].set_minfilter(Texture.FT_linear)
            self._target["color"].set_magfilter(Texture.FT_linear)

            self._target_sharpen.set_shader_input("SourceTex", self._target["color"])

        else:
            # Make the main target the only target
            self._target.set_color_write(True)
            self._target.prepare_offscreen_buffer()
            self._target.make_main_target()

    def set_shaders(self):
        self._target.set_shader(self.load_plugin_shader("CorrectColor.frag.glsl"))
        if self._use_sharpen:
            self._target_sharpen.set_shader(self.load_plugin_shader("Sharpen.frag.glsl"))

    def resize(self):
        RenderStage.resize(self)
        self.debug("Resizing pass")

    def cleanup(self):
        RenderStage.cleanup(self)
        self.debug("Cleanup pass")
