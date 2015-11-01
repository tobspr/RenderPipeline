
from ..RenderStage import RenderStage


class ColorCorrectionStage(RenderStage):

    """ This stage does the SRGB correction and further postprocess color
    correction effects"""

    required_pipes = ["ShadedScene"]

    def __init__(self, pipeline):
        RenderStage.__init__(self, "ColorCorrectionStage", pipeline)

    def get_produced_pipes(self):
        return {"ColorCorrectedScene": self._target["color"]}

    def create(self):
        self._target = self._create_target("ColorCorrection")
        self._target.add_color_texture(bits=16)
        self._target.prepare_offscreen_buffer()

    def set_shaders(self):
        self._target.set_shader(self._load_shader("Stages/CorrectColor.frag"))

    def resize(self):
        RenderStage.resize(self)
        self.debug("Resizing pass")

    def cleanup(self):
        RenderStage.cleanup(self)
        self.debug("Cleanup pass")
