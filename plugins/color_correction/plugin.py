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

from panda3d.core import SamplerState

# Load the plugin api
from .. import *
from .color_correction_stage import ColorCorrectionStage
from .auto_exposure_stage import AutoExposureStage

class Plugin(BasePlugin):

    @PluginHook("on_stage_setup")
    def setup_stages(self):

        # Disable default display stage to use our own stage
        get_internal_stage("final_stage", "FinalStage").disable_stage()

        self._stage = self.create_stage(ColorCorrectionStage)
        self._stage.set_use_sharpen(self.get_setting("use_sharpen"))

        if self.get_setting("use_auto_exposure"):
            self._exposure_stage = self.create_stage(AutoExposureStage)

    @PluginHook("on_pipeline_created")
    def pipeline_created(self):
        self._load_lut()

    def _load_lut(self):
        lut_path = self.get_resource("default_lut.png")
        lut = SliceLoader.load_3d_texture(lut_path, 64)
        lut.set_wrap_u(SamplerState.WM_clamp)
        lut.set_wrap_v(SamplerState.WM_clamp)
        lut.set_wrap_w(SamplerState.WM_clamp)
        lut.set_minfilter(SamplerState.FT_linear)
        lut.set_magfilter(SamplerState.FT_linear)
        lut.set_anisotropic_degree(0)
        self._stage.set_shader_input("ColorLUT", lut)
