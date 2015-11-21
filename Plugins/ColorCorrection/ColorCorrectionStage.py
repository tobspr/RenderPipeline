
from .. import *

class ColorCorrectionStage(RenderStage):

    required_pipes = ["ShadedScene"]
    required_inputs = ["TimeOfDay", "mainCam", "mainRender", "cameraPosition"]

    def __init__(self, pipeline):
        RenderStage.__init__(self, "ColorCorrectionStage", pipeline)

    def create(self):
        self._target = self._create_target("ColorCorrectionStage")
        self._target.prepare_offscreen_buffer()
        self._target.make_main_target()

    def set_shaders(self):
        self._target.set_shader(self.load_plugin_shader("CorrectColor.frag.glsl"))

    def resize(self):
        RenderStage.resize(self)
        self.debug("Resizing pass")

    def cleanup(self):
        RenderStage.cleanup(self)
        self.debug("Cleanup pass")
