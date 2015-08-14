 

from panda3d.core import NodePath, Shader, LVecBase2i, Texture, GeomEnums

from ..Globals import Globals
from ..RenderPass import RenderPass
from ..RenderTarget import RenderTarget

class BloomPass(RenderPass):

    """ This pass extracts bright parts from the scene, blurs them and then
    merges them back. """

    def __init__(self):
        RenderPass.__init__(self)

    def getID(self):
        return "BloomPass"

    def getRequiredInputs(self):
        return {
            "colorTex": ["DOFPass.resultTex", "ExposurePass.resultTex", "SSLRPass.resultTex", "TransparencyPass.resultTex", "LightingPass.resultTex"],
            "mainRender": "Variables.mainRender",
            "mainCam": "Variables.mainCam",
            "skyboxMask": "SkyboxMaskPass.resultTex"
        }

    def create(self):
        self.target = RenderTarget("BloomExtract")
        self.target.setQuarterResolution()
        self.target.addColorTexture()
        self.target.setColorBits(16)
        self.target.prepareOffscreenBuffer()
 
        self.targetV = RenderTarget("BloomBlurV")
        self.targetV.setQuarterResolution()
        self.targetV.addColorTexture()
        self.targetV.setColorBits(16)
        self.targetV.prepareOffscreenBuffer()
 
        self.targetH = RenderTarget("BloomBlurH")
        self.targetH.setQuarterResolution()
        self.targetH.addColorTexture()
        self.targetH.setColorBits(16)
        self.targetH.prepareOffscreenBuffer()


        self.targetMerge = RenderTarget("MergeBloom")
        self.targetMerge.addColorTexture()
        self.targetMerge.setColorBits(16)
        self.targetMerge.prepareOffscreenBuffer()

        self.targetV.setShaderInput("bloomTex", self.target.getColorTexture())
        self.targetH.setShaderInput("bloomTex", self.targetV.getColorTexture())
        self.targetMerge.setShaderInput("bloomTex", self.targetH.getColorTexture())

    def setShaders(self):
        shader = Shader.load(Shader.SLGLSL, 
            "Shader/DefaultPostProcess.vertex",
            "Shader/BloomExtract.fragment")
        self.target.setShader(shader)

        shaderV = Shader.load(Shader.SLGLSL, 
            "Shader/DefaultPostProcess.vertex",
            "Shader/BloomBlurV.fragment")
        self.targetV.setShader(shaderV)

        shaderH = Shader.load(Shader.SLGLSL, 
            "Shader/DefaultPostProcess.vertex",
            "Shader/BloomBlurH.fragment")
        self.targetH.setShader(shaderH)
        
        shaderMerge = Shader.load(Shader.SLGLSL, 
            "Shader/DefaultPostProcess.vertex",
            "Shader/BloomMerge.fragment")
        self.targetMerge.setShader(shaderMerge)

        return [shader, shaderV, shaderH]

    def setShaderInput(self, *args):
        self.target.setShaderInput(*args)
        self.targetV.setShaderInput(*args)
        self.targetH.setShaderInput(*args)
        self.targetMerge.setShaderInput(*args)

    def getOutputs(self):
        return {
            "BloomPass.resultTex": lambda: self.targetMerge.getColorTexture(),
        }
