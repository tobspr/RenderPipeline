
from ..RenderStage import RenderStage


class DownscaleZStage(RenderStage):

    """ This stage downscales the z buffer """

    def __init__(self, pipeline):
        RenderStage.__init__(self, "DownscaleZStage", pipeline)

    def get_produced_pipes(self):
        return {
            "DownscaledDepth": self._target['color']
        }

    def get_input_pipes(self):
        return ["GBufferDepth"]


    def create(self):
        self._target = self._create_target("DownscaleZ")
        self._target.add_color_texture()
        self._target.set_color_bits(32)
        self._target.prepare_offscreen_buffer()

    def set_shaders(self):
        self._target.set_shader(
            self._load_shader("Stages/DownscaleZ.frag"))

    def resize(self):
        RenderStage.resize(self)
        self.debug("Resizing pass")

    def cleanup(self):
        RenderStage.cleanup(self)
        self.debug("Cleanup pass")
