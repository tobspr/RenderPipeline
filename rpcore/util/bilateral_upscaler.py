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

from panda3d.core import Vec4

from rpcore.rpobject import RPObject
from rpcore.image import Image
from rpcore.globals import Globals

class BilateralUpscaler(RPObject):
    """ Class for creating bilateral upscale targets, with features like filling
    invalid pixels """

    # Controls how many entries to process in one row. Needs to match the
    # definition in the fillin shader
    ROW_WIDTH = 512

    def __init__(self, parent_stage, halfres=False, source_tex=None, name="", percentage=0.05):
        """ Creates a new upscaler with the given name. Percentage controls
        the maximum amount of invalid pixels which can be processed, for example
        a value of 0.05 means that 5% of all pixels may be invalid. """
        RPObject.__init__(self)
        self.name = name
        self.halfres = halfres
        self.parent_stage = parent_stage
        self.percentage = percentage
        self.source_tex = source_tex
        self._prepare_textures()
        self._prepare_target()

    def _prepare_textures(self):
        """ Prepares all required textures """
        self.counter = Image.create_counter(self.name + ":BadPixelsCounter")
        self.counter.set_clear_color(Vec4(0))
        self.databuffer = Image.create_buffer(self.name + ":BadPixelsData", 1, "R32I")
    
    def _prepare_target(self):
        """ Prepares all required render targets """
        self.target_upscale = self.parent_stage.create_target(self.name + ":Upscale")
        self.target_upscale.size = "50%" if self.halfres else "100%"
        self.target_upscale.add_color_attachment(bits=(8, 0, 0, 0))
        self.target_upscale.prepare_buffer()
        self.target_upscale.set_shader_input("InvalidPixelCounter", self.counter)
        self.target_upscale.set_shader_input("InvalidPixelBuffer", self.databuffer)
        self.target_upscale.set_shader_input("SourceTex", self.source_tex)

        self.target_fillin = self.parent_stage.create_target(self.name + ":Fillin")
        self.target_fillin.size = 0, 0
        self.target_fillin.prepare_buffer()
        self.target_fillin.set_shader_input("pixel_multiplier", 2 if self.halfres else 1)
        self.target_fillin.set_shader_input("InvalidPixelCounter", self.counter)
        self.target_fillin.set_shader_input("InvalidPixelBuffer", self.databuffer)
        self.target_fillin.set_shader_input("DestTex", self.target_upscale.color_tex)

    @property
    def result_tex(self):
        """ Returns the final upscaled texture """
        return self.target_upscale.color_tex

    def set_shaders(self, upscale_shader, fillin_shader):
        """ Sets all required shaders """
        self.target_upscale.shader = upscale_shader
        self.target_fillin.shader = fillin_shader
        
    def set_dimensions(self):
        """ Adapts the targets to the current resolution """
        pixels = max(1, int(Globals.resolution.x * Globals.resolution.y * self.percentage))
        self.databuffer.setup_buffer(pixels, "R32I")
        self.target_fillin.size = self.ROW_WIDTH, pixels // self.ROW_WIDTH

    def update(self):
        """ Updates all targets and buffers """
        self.counter.clear_image()
