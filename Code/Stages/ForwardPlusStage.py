
from panda3d.core import Shader

from ..RenderStage import RenderStage

class ForwardPlusStage(RenderStage):

    def __init__(self, pipeline):
        RenderStage.__init__(self, "ForwardPlusStage", pipeline)

    def getProducedPipes(self):
        return {
            "ShadedScene": self.target.getColorTexture()
        }

    def getInputPipes(self):
        return ["CellIndices", "PerCellLights"]

    def getRequiredInputs(self):
        return ["AllLightsData", "cameraPosition"]

    def create(self):
        self.target = self._createTarget("ForwardPlusStage")
        self.target.addDepthTexture()
        self.target.addColorTexture()
        self.target.setDepthBits(32)
        self.target.setColorBits(16)
        self.target.prepareSceneRender()
        self.target.setClearDepth(True)

    def setShaders(self):
        render.setShader(Shader.load(Shader.SLGLSL, "Shader/Templates/Vertex.glsl", 
            "Shader/Templates/Stages/ForwardPlus-Fragment.glsl"))

    def setShaderInput(self, *args):
        render.setShaderInput(*args)

    def resize(self):
        self.debug("Resizing pass")

    def cleanup(self):
        self.debug("Cleanup pass")
