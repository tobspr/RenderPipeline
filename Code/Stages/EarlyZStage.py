
from ..RenderStage import RenderStage
from ..Util.RenderTarget import RenderTarget

class EarlyZStage(RenderStage):

    def __init__(self, pipeline):
        RenderStage.__init__(self, "EarlyZStage", pipeline)

    def getRequiredInputs(self):
        return {}

    def getInputPipes(self):
        return []

    def getProducedPipes(self):
        return {
            "GBufferDepth": self.target.getDepthTexture()
        }

    def create(self):
        self.target = self._createTarget("EarlyZPass")
        self.target.addDepthTexture()
        self.target.setDepthBits(32)
        self.target.prepareSceneRender()
        self.target.setClearDepth(True)

    def resize(self):
        self.debug("Resizing pass")

    def cleanup(self):
        self.debug("Cleanup pass")
    


