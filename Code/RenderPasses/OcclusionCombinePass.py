
from panda3d.core import NodePath, Shader, LVecBase2i, Texture, GeomEnums

from ..Globals import Globals
from ..RenderPass import RenderPass
from ..RenderTarget import RenderTarget

class OcclusionCombinePass(RenderPass):

    """ This pass merges the current frame occlusion with the last frame occlusion """

    def __init__(self):
        RenderPass.__init__(self)

    def getID(self):
        return "OcclusionCombinePass"

    def getRequiredInputs(self):
        return {
            "velocityTex": "DeferredScenePass.velocity",

            "currentOcclusionTex":  ["OcclusionBlurPass.blurResult", "AmbientOcclusionPass.computeResult"], 
            "lastFrameDepth": ["Variables.lastFrameDepth", "Variables.emptyTextureWhite"],
            "lastFrameOcclusion": ["Variables.lastFrameOcclusion", "Variables.emptyTextureWhite"],
            "currentMVP": "Variables.currentMVP",
            "lastMVP": "Variables.lastMVP",
        }

    def create(self):
        self.target = RenderTarget("OcclusionCombine")
        self.target.addColorTexture()
        self.target.prepareOffscreenBuffer()
 

    def setShaders(self):
        shader = Shader.load(Shader.SLGLSL, 
            "Shader/DefaultPostProcess.vertex",
            "Shader/CombineOcclusion.fragment")
        self.target.setShader(shader)

        return [shader]

    def getOutputs(self):
        return {
            "OcclusionCombinePass.resultTex": lambda: self.target.getColorTexture(),
        }

