

from panda3d.core import Texture

# Load the plugin api
from .. import *
from .ColorCorrectionStage import ColorCorrectionStage
from .AutoExposureStage import AutoExposureStage

class Plugin(BasePlugin):

    @PluginHook("on_stage_setup")
    def setup_stages(self):

        # Disable default display stage to use our own stage
        get_internal_stage("FinalStage").disable_stage()

        self._stage = self.create_stage(ColorCorrectionStage)
        self._stage.set_use_sharpen(self.get_setting("use_sharpen"))

        if self.get_setting("use_auto_exposure"):
            self._exposure_stage = self.create_stage(AutoExposureStage)

    @PluginHook("on_pipeline_created")
    def pipeline_created(self):
        self._load_lut()

    def _load_lut(self):
        lut_path = self.get_resource("DefaultLUT.png")
        lut = SliceLoader.load_3d_texture(lut_path, 64)
        lut.set_wrap_u(Texture.WM_clamp)
        lut.set_wrap_v(Texture.WM_clamp)
        lut.set_wrap_w(Texture.WM_clamp)
        lut.set_minfilter(Texture.FT_linear)
        lut.set_magfilter(Texture.FT_linear)
        lut.set_anisotropic_degree(0)
        self._stage.set_shader_input("ColorLUT", lut)
