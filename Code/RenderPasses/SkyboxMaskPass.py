
from panda3d.core import NodePath, Shader, LVecBase2i, Texture, GeomEnums

from ..Globals import Globals
from ..RenderPass import RenderPass
from ..RenderTarget import RenderTarget

class SkyboxMaskPass(RenderPass):

    """ This pass outputs a mask for the scene, storing wheter a material is a skybox
    or not """

    def __init__(self):
        RenderPass.__init__(self)

    def getID(self):
        return "SkyboxMaskPass"

    def getRequiredInputs(self):
        return {
            "depthTex": "DeferredScenePass.depth"
        }

    def create(self):
        self.target = RenderTarget("MaskSkybox")
        self.target.addColorTexture()
        self.target.prepareOffscreenBuffer()
 
    def setShaders(self):
        shader = Shader.load(Shader.SLGLSL, 
            "Shader/DefaultPostProcess.vertex",
            "Shader/SkyboxMask.fragment")
        self.target.setShader(shader)

        return [shader]

    def getOutputs(self):
        return {
            "SkyboxMaskPass.resultTex": lambda: self.target.getColorTexture(),
        }
