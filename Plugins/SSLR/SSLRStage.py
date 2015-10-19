
from .. import RenderStage


class SSLRStage(RenderStage):

    """ This stage does the SSLR pass """

    def __init__(self, pipeline):
        RenderStage.__init__(self, "SSLRStage", pipeline)

    def get_produced_pipes(self):
        return {
            "ShadedScene": self._target['color']
        }

    def get_input_pipes(self):
        return ["ShadedScene", "GBufferDepth", "GBuffer0", "GBuffer1",
                "GBuffer2", "DownscaledDepth"]

    def get_required_inputs(self):
        return ["mainCam", "mainRender", "cameraPosition", "currentViewProjMat"]

    def create(self):
        self._target = self._create_target("SSLRStage")
        self._target.add_color_texture()
        self._target.set_color_bits(16)
        self._target.prepare_offscreen_buffer()

    def set_shaders(self):
        self._target.set_shader(
            self._load_plugin_shader("SSLR", "SSLRStage.frag.glsl"))

    def resize(self):
        RenderStage.resize(self)
        self.debug("Resizing pass")

    def cleanup(self):
        RenderStage.cleanup(self)
        self.debug("Cleanup pass")
