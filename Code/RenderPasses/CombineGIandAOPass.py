

from panda3d.core import NodePath, Shader, LVecBase2i, Texture, GeomEnums

from Code.Globals import Globals
from Code.RenderPass import RenderPass
from Code.RenderTarget import RenderTarget

class CombineGIandAOPass(RenderPass):

    """ This pass combines the global illumination and ambient occlusion textures,
    to be able to blur them both in one step """

    def __init__(self):
        RenderPass.__init__(self)

    def getID(self):
        return "CombineGIandAOPass"

    def getRequiredInputs(self):
        return {
            "aoResultTex":  "AmbientOcclusionPass.computeResult", 
            "giResultTex": "GlobalIlluminationPass.diffuseResult"
        }

    def create(self):
        self.target = RenderTarget("CombineGIandAOPass")
        self.target.setHalfResolution()
        self.target.addColorTexture()
        self.target.setColorBits(16)
        self.target.prepareOffscreenBuffer()

    def setShaders(self):
        shader = Shader.load(Shader.SLGLSL, 
            "Shader/DefaultPostProcess.vertex",
            "Shader/CombineGIandAO.fragment")
        self.target.setShader(shader)

    def getOutputs(self):
        return {
            "CombineGIandAOPass.combinedTex": lambda: self.target.getColorTexture(),
        }

