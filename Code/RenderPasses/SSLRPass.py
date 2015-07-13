
from panda3d.core import NodePath, Shader, LVecBase2i, Texture, GeomEnums

from ..Globals import Globals
from ..RenderPass import RenderPass
from ..RenderTarget import RenderTarget

class SSLRPass(RenderPass):

    """ This pass computes screen space local reflections and applies it to the
    scene """

    def __init__(self):
        RenderPass.__init__(self)

    def getID(self):
        return "SSLRPass"

    def getRequiredInputs(self):
        return {

            "normalTex": "DeferredScenePass.wsNormal",
            "positionTex": "DeferredScenePass.wsPosition",
            "depthTex": "DeferredScenePass.depth",

            "currentMVP": "Variables.currentMVP",
            "cameraPosition": "Variables.cameraPosition",

            "mainCam": "Variables.mainCam",
            "mainRender": "Variables.mainRender",

            "colorTex": ["TransparencyPass.resultTex", "LightingPass.resultTex"]
        }

    def create(self):
        self.target = RenderTarget("SSLR")
        # self.target.setHalfResolution()
        self.target.addColorTexture()
        self.target.setColorBits(16)
        self.target.prepareOffscreenBuffer()
 
        self.targetV = RenderTarget("SSLRBlurV")
        self.targetV.addColorTexture()
        self.targetV.setColorBits(16)
        self.targetV.prepareOffscreenBuffer()
 
        self.targetH = RenderTarget("SSLRBlurH")
        self.targetH.addColorTexture()
        self.targetH.setColorBits(16)
        self.targetH.prepareOffscreenBuffer()

        self.targetV.setShaderInput("previousTex", self.target.getColorTexture())
        self.targetH.setShaderInput("previousTex", self.targetV.getColorTexture())



    def setShaders(self):
        shader = Shader.load(Shader.SLGLSL, 
            "Shader/DefaultPostProcess.vertex",
            "Shader/SSLRPass.fragment")
        self.target.setShader(shader)

        shaderV = Shader.load(Shader.SLGLSL, 
            "Shader/DefaultPostProcess.vertex",
            "Shader/SSLRBlurV.fragment")
        self.targetV.setShader(shaderV)

        shaderH = Shader.load(Shader.SLGLSL, 
            "Shader/DefaultPostProcess.vertex",
            "Shader/SSLRBlurH.fragment")
        self.targetH.setShader(shaderH)


        return [shader, shaderV, shaderH]

    def setShaderInput(self, name, value):
        self.target.setShaderInput(name, value)
        self.targetH.setShaderInput(name, value)
        self.targetV.setShaderInput(name, value)



    def getOutputs(self):
        return {
            "SSLRPass.resultTex": lambda: self.targetH.getColorTexture(),
        }
