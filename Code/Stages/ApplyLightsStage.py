
from panda3d.core import Texture, Shader

from ..RenderStage import RenderStage
from ..Util.RenderTarget import RenderTarget
from ..Util.Image import Image
from ..Globals import Globals

class ApplyLightsStage(RenderStage):

    def __init__(self, pipeline):
        RenderStage.__init__(self, "ApplyLightsStage", pipeline)

    def getInputPipes(self):
        return ["GBufferDepth", "CellIndices", "PerCellLights"]

    def getProducedPipes(self):
        return {"ShadedScene": self.target.getColorTexture()}


    def getRequiredInputs(self):
        return [
            "AllLightsData",
            "mainCam",
            "mainRender"
         ]

    def create(self):

        self.target = self._createTarget("ApplyLights")
        self.target.addColorTexture()
        self.target.prepareOffscreenBuffer()

        # Make this pass show on the screen
        Globals.base.win.getDisplayRegion(1).setCamera(self.target._camera)


    def update(self):
        pass

    def setShaders(self):
        self.target.setShader(self._loadShader("Stages/ApplyLights.fragment"))

    def resize(self):
        self.debug("Resizing pass")

    def cleanup(self):
        self.debug("Cleanup pass")
    


