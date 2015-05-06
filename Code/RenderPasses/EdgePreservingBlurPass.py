
from panda3d.core import NodePath, Shader, LVecBase2i, Texture, GeomEnums

from Code.Globals import Globals
from Code.RenderPass import RenderPass
from Code.RenderTarget import RenderTarget

class EdgePreservingBlurPass(RenderPass):

    def __init__(self):
        RenderPass.__init__(self)

    def getID(self):
        return "EdgePreservingBlurPass"

    def getRequiredInputs(self):
        return {
            "sourceTex":  [
                "CombineGIandAOPass.combinedTex",  # If both GI and AO are active, this pass exists
                "AmbientOcclusionPass.computeResult", 
                "GlobalIlluminationPass.diffuseResult"],
            "normalTex": "DeferredScenePass.wsNormal"
        }

    def create(self):
        self.targetV = RenderTarget("EdgePreservingBlurV")
        self.targetV.addColorTexture()
        self.targetV.setColorBits(16)
        self.targetV.prepareOffscreenBuffer()
 
        self.targetH = RenderTarget("EdgePreservingBlurH")
        self.targetH.addColorTexture()
        self.targetH.setColorBits(16)
        self.targetH.prepareOffscreenBuffer()

        self.targetH.setShaderInput("processedSourceTex", self.targetV.getColorTexture())

    def setShaders(self):
        shaderV = Shader.load(Shader.SLGLSL, 
            "Shader/DefaultPostProcess.vertex",
            "Shader/EdgePreservingBlurVertical.fragment")
        self.targetV.setShader(shaderV)

        shaderH = Shader.load(Shader.SLGLSL, 
            "Shader/DefaultPostProcess.vertex",
            "Shader/EdgePreservingBlurHorizontal.fragment")
        self.targetH.setShader(shaderH)

    def getOutputs(self):
        return {
            "EdgePreservingBlurPass.blurResult": lambda: self.targetH.getColorTexture(),
        }

    def setShaderInput(self, name, value):
        self.targetH.setShaderInput(name, value)
        self.targetV.setShaderInput(name, value)
