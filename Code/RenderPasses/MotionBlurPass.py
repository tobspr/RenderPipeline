
from panda3d.core import NodePath, Shader, LVecBase2i, Texture, GeomEnums

from ..Globals import Globals
from ..RenderPass import RenderPass
from ..RenderTarget import RenderTarget

class MotionBlurPass(RenderPass):

    """ This pass computes motion blur using the velocity texture """

    def __init__(self):
        RenderPass.__init__(self)

    def getID(self):
        return "MotionBlurPass"

    def getRequiredInputs(self):
        return {
            "worldSpaceNormals": "DeferredScenePass.wsNormal",
            "worldSpacePosition": "DeferredScenePass.wsPosition",
            "depthTex": "DeferredScenePass.depth",
            "velocityTex": "DeferredScenePass.velocity",
            "frameDelta": "Variables.frameDelta",
            "colorTex": ["AntialiasingPass.resultTex", "SSLRPass.resultTex", "TransparencyPass.resultTex", "LightingPass.resultTex"],
        }

    def create(self):

        self.targetDilate = RenderTarget("MotionBlurDilateVelocity")
        self.targetDilate.addColorTexture()
        self.targetDilate.setColorBits(16)
        self.targetDilate.prepareOffscreenBuffer()

        self.target = RenderTarget("MotionBlur")
        self.target.addColorTexture()
        self.target.prepareOffscreenBuffer()
        self.target.setShaderInput("dilatedVelocityTex", self.targetDilate.getColorTexture())


    def setShaders(self):
        shader = Shader.load(Shader.SLGLSL, 
            "Shader/DefaultPostProcess.vertex",
            "Shader/MotionBlur.fragment")
        self.target.setShader(shader)

        shaderDilate = Shader.load(Shader.SLGLSL, 
            "Shader/DefaultPostProcess.vertex",
            "Shader/MotionBlurDilate.fragment")
        self.targetDilate.setShader(shaderDilate)

        return [shader, shaderDilate]

    def setShaderInput(self, name, value):
        self.target.setShaderInput(name, value)
        self.targetDilate.setShaderInput(name, value)


    def getOutputs(self):
        return {
            "MotionBlurPass.resultTex": lambda: self.target.getColorTexture(),
        }
