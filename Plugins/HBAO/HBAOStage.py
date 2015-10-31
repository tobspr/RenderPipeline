
from .. import RenderStage

class HBAOStage(RenderStage):

    def __init__(self, pipeline):
        RenderStage.__init__(self, "HBAOStage", pipeline)

    def get_produced_pipes(self):
        return {
            "ShadedScene": self._target['color']
        }

    def get_input_pipes(self):
        return ["ShadedScene", "GBufferDepth"]

    def get_required_inputs(self):
        return ["mainCam", "mainRender"]

    def create(self):
        self._target = self._create_target("HBAODownscaleDepth")
        self._target.add_color_texture()
        self._target.set_color_bits(16)
        self._target.prepare_offscreen_buffer()
        
    def set_shaders(self):
        self._target.set_shader(
            self._load_shader("Stages/AmbientStage.frag"))

    def resize(self):
        RenderStage.resize(self)
        self.debug("Resizing pass")

    def cleanup(self):
        RenderStage.cleanup(self)
        self.debug("Cleanup pass")
