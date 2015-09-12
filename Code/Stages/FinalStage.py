
from ..RenderStage import RenderStage
from ..Util.RenderTarget import RenderTarget

class FinalStage(RenderStage):

    def __init__(self, pipeline):
        RenderStage.__init__(self, "FinalStage", pipeline)

    def getProducedPipes(self):
        return {}

    def getInputPipes(self):
        return ["ShadedScene"]

    def create(self):
        self.target = self._createTarget("FinalStage")
        self.target.addColorTexture()
        self.target.prepareOffscreenBuffer()
        self.target.makeMainTarget()

    def setShaders(self):
        self.target.setShader(self._loadShader("Stages/FinalStage.fragment"))

    def resize(self):
        self.debug("Resizing pass")

    def cleanup(self):
        self.debug("Cleanup pass")
    



