
from panda3d.core import NodePath, Shader, LVecBase2i, Texture, GeomEnums, ColorBlendAttrib

from ..Globals import Globals
from ..RenderPass import RenderPass
from ..RenderTarget import RenderTarget
from ..MemoryMonitor import MemoryMonitor

class DOFPass(RenderPass):

    """ This pass applies the depth of field blur """

    def __init__(self):
        RenderPass.__init__(self)

    def getID(self):
        return "DOFPass"

    def getRequiredInputs(self):
        return {
            "colorTex": ["ExposurePass.resultTex"],
            "depthTex": "DeferredScenePass.depth",
            "skyboxMask": "SkyboxMaskPass.resultTex",
            "cameraPosition": "Variables.cameraPosition",
            "mainCam": "Variables.mainCam",
            "mainRender": "Variables.mainRender"
        }

    def create(self):
        self.targetCoC = RenderTarget("DOF-CoC")
        self.targetCoC.setColorBits(16)
        self.targetCoC.setAuxBits(16)
        self.targetCoC.addColorTexture()
        self.targetCoC.addAuxTexture()
        self.targetCoC.prepareOffscreenBuffer()

        if False:
            self.targetSpawnSprites = RenderTarget("DOF-Sprites")
            # self.targetSpawnSprites.setHalfResolution()
            self.targetSpawnSprites.addColorTexture()
            self.targetSpawnSprites.setColorBits(16)
            self.targetSpawnSprites.prepareOffscreenBuffer()
            self.targetSpawnSprites.setClearColor(True)

            quad = self.targetSpawnSprites.getQuad()
            quad.setDepthTest(False)
            quad.setDepthWrite(False)
            quad.setAttrib(ColorBlendAttrib.make(ColorBlendAttrib.MAdd))

            w, h = int(Globals.resolution.x / 1), int(Globals.resolution.y / 1)

            bokehTex = loader.loadTexture("Data/Textures/BokehShape.png")
            bokehTex.setMinfilter(Texture.FTLinear)
            bokehTex.setMagfilter(Texture.FTLinear)
            bokehTex.setWrapU(Texture.WMClamp)
            bokehTex.setWrapV(Texture.WMClamp)
            bokehTex.setAnisotropicDegree(0)
            quad.setShaderInput("bokehTex", bokehTex)
            quad.setShaderInput("sourceTex", self.targetCoC.getColorTexture())
            quad.setInstanceCount(w * h) # Poor GPU

        self.targetBlurV = RenderTarget("DOF-BlurV")
        self.targetBlurV.setColorBits(16)
        self.targetBlurV.addColorTexture()
        self.targetBlurV.prepareOffscreenBuffer()
        self.targetBlurV.setShaderInput("sourceBlurTex", self.targetCoC.getAuxTexture(0))
        
        self.targetBlurH = RenderTarget("DOF-BlurH")
        self.targetBlurH.setColorBits(16)
        self.targetBlurH.addColorTexture()
        self.targetBlurH.prepareOffscreenBuffer()
        self.targetBlurH.setShaderInput("sourceBlurTex", self.targetBlurV.getColorTexture())
        
        self.targetCombine = RenderTarget("DOF-Combine")
        self.targetCombine.addColorTexture()
        self.targetCombine.setColorBits(16)
        self.targetCombine.prepareOffscreenBuffer()

        self.targetCombine.setShaderInput("sceneBlurTex", self.targetBlurH.getColorTexture())
        # self.targetCombine.setShaderInput("spriteTex", self.targetSpawnSprites.getColorTexture())

    def setShaders(self):
        shaderCoC = Shader.load(Shader.SLGLSL, 
            "Shader/DefaultPostProcess.vertex",
            "Shader/DoF/DoFCoC.fragment")
        self.targetCoC.setShader(shaderCoC)
        
        # shaderSprites = Shader.load(Shader.SLGLSL, 
        #     "Shader/DoF/DoFSprite.vertex",
        #     "Shader/DoF/DoFSprite.fragment")
        # self.targetSpawnSprites.setShader(shaderSprites)

        shaderBlurV = Shader.load(Shader.SLGLSL, 
            "Shader/DefaultPostProcess.vertex",
            "Shader/DoF/DoFBlurV.fragment")
        self.targetBlurV.setShader(shaderBlurV)

        shaderBlurH = Shader.load(Shader.SLGLSL, 
            "Shader/DefaultPostProcess.vertex",
            "Shader/DoF/DoFBlurH.fragment")
        self.targetBlurH.setShader(shaderBlurH)

        shaderCombine = Shader.load(Shader.SLGLSL, 
            "Shader/DefaultPostProcess.vertex",
            "Shader/DoF/DoFCombine.fragment")
        self.targetCombine.setShader(shaderCombine)        
        
        return [shaderCoC, shaderBlurV, shaderBlurH, shaderCombine]

    def setShaderInput(self, *args):
        self.targetCoC.setShaderInput(*args)
        self.targetBlurH.setShaderInput(*args)
        self.targetBlurV.setShaderInput(*args)
        self.targetCombine.setShaderInput(*args)

    def getOutputs(self):
        return {
            "DOFPass.resultTex": lambda: self.targetCombine.getColorTexture(),
        }


