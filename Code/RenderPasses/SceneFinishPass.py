
from panda3d.core import NodePath, Shader, LVecBase2i, Texture, PTAFloat, Vec4

from ..Globals import Globals
from ..RenderPass import RenderPass
from ..RenderTarget import RenderTarget

class SceneFinishPass(RenderPass):

    """ This pass copies the current frame textures to the last frame textures. """

    def __init__(self):
        RenderPass.__init__(self)

    def getID(self):
        return "SceneFinishPass"

    def getRequiredInputs(self):
        return {
            "colorTex": ["MotionBlurPass.resultTex", "AntialiasingPass.resultTex", "SSLRPass.resultTex", "TransparencyPass.resultTex", "LightingPass.resultTex"],
            "colorLUT": "Variables.colorLUT",
            "velocityTex": "DeferredScenePass.velocity",
            "depthTex": "DeferredScenePass.depth",
            "lastFrameDepthTex": "Variables.lastFrameDepth",
            "lastFrameOcclusionTex": ["Variables.lastFrameOcclusion", "Variables.emptyTextureWhite"],
            "currentOcclusionTex": ["OcclusionCombinePass.resultTex", "Variables.emptyTextureWhite"]
        }

    def create(self):
        self.target = RenderTarget("Scene Finish Pass")
        self.target.addColorTexture()
        self.target.prepareOffscreenBuffer()

    def setShaders(self):
        shader = Shader.load(Shader.SLGLSL, 
            "Shader/DefaultPostProcess.vertex",
            "Shader/SceneFinishPass.fragment")
        self.target.setShader(shader)

        return [shader]
