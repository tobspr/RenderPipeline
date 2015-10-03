
from ..RenderStage import RenderStage


class AmbientStage(RenderStage):

    """ This stage computes the ambient term """

    def __init__(self, pipeline):
        RenderStage.__init__(self, "AmbientStage", pipeline)

    def get_produced_pipes(self):
        return {
            "ShadedScene": self._target.getColorTexture()
        }

    def get_input_pipes(self):
        return ["ShadedScene", "GBufferDepth", "GBuffer0", "GBuffer1",
                "GBuffer2"]

    def get_required_inputs(self):
        return ["mainCam", "mainRender"]

    def create(self):
        self._target = self._create_target("AmbientStage")
        self._target.addColorTexture()
        self._target.setColorBits(16)
        self._target.prepareOffscreenBuffer()
        self._target.setClearDepth(True)

    def set_shaders(self):
        self._target.setShader(
            self._load_shader("Stages/AmbientStage.fragment"))

    def resize(self):
        RenderStage.resize(self)
        self.debug("Resizing pass")

    def cleanup(self):
        RenderStage.cleanup(self)
        self.debug("Cleanup pass")
