
from panda3d.core import NodePath, Shader, LVecBase2i, Texture, PTAFloat, Vec4

from Code.Globals import Globals
from Code.RenderPass import RenderPass
from Code.RenderTarget import RenderTarget

class DynamicExposurePass(RenderPass):

    def __init__(self, pipeline):
        RenderPass.__init__(self)

        self.pipeline = pipeline
        self.targetExposure = PTAFloat.emptyArray(1)
        self.targetExposure[0] = 0.5
        self.adaptionSpeed = PTAFloat.emptyArray(1)
        self.adaptionSpeed[0] = 1.0

        self.lastExposureStorage = Texture("Last Exposure")
        self.lastExposureStorage.setup2dTexture(1, 1, Texture.TFloat, Texture.FR32)

        self.pipeline.renderPassManager.registerStaticVariable(
            "dynamicExposureTex", self.lastExposureStorage)
        self.pipeline.renderPassManager.registerDefine("USE_ADAPTIVE_BRIGHTNESS", 1)

    def getID(self):
        return "DynamicExposurePass"

    def getRequiredInputs(self):
        return {
            "colorTex": "LightingPass.resultTex",
            "dt": "Variables.frameDelta"
        }


    def create(self):
        size = LVecBase2i(Globals.base.win.getXSize(), Globals.base.win.getYSize())

        self.downscalePass0 = RenderTarget("Downscale Initial")
        self.downscalePass0.addColorTexture()
        self.downscalePass0.setSize(size.x / 2, size.y / 2)
        self.downscalePass0.prepareOffscreenBuffer()

        workSizeX, workSizeY = int(size.x / 2), int(size.y / 2)

        self.downscalePasses = []
        passIdx = 0
        lastTex = self.downscalePass0.getColorTexture()

        while workSizeX * workSizeY > 128:
            workSizeX /= 4
            workSizeY /= 4
            passIdx += 1
            scalePass = RenderTarget("Downscale Pass " + str(passIdx))
            scalePass.setSize(workSizeX, workSizeY)
            scalePass.addColorTexture()
            scalePass.prepareOffscreenBuffer()
            scalePass.setShaderInput("luminanceTex", lastTex)
            lastTex = scalePass.getColorTexture()
            self.downscalePasses.append(scalePass)

        self.finalDownsamplePass = RenderTarget("Downscale Final")
        self.finalDownsamplePass.setSize(1, 1)
        self.finalDownsamplePass.setColorBits(16)
        self.finalDownsamplePass.addColorTexture()
        self.finalDownsamplePass.prepareOffscreenBuffer()
        self.finalDownsamplePass.setShaderInput("luminanceTex", lastTex)
        self.finalDownsamplePass.setShaderInput("targetExposure", self.targetExposure)
        self.finalDownsamplePass.setShaderInput("adaptionSpeed", self.adaptionSpeed)

        self.lastExposureStorage.setClearColor(Vec4(self.targetExposure[0]))
        self.lastExposureStorage.clearImage()

        self.finalDownsamplePass.setShaderInput("lastExposureTex", self.lastExposureStorage)

    def setShaders(self):
        """ Reloads the shaders for the various passes """
        fpShader = Shader.load(Shader.SLGLSL, 
            "Shader/DefaultPostProcess.vertex",
            "Shader/AdaptiveBrightnessFirstPass.fragment")
        self.downscalePass0.setShader(fpShader)

        dsShader = Shader.load(Shader.SLGLSL, 
            "Shader/DefaultPostProcess.vertex",
            "Shader/AdaptiveBrightnessDownsample.fragment")
        for scalePass in self.downscalePasses:
            scalePass.setShader(dsShader)

        fpShader = Shader.load(Shader.SLGLSL, 
            "Shader/DefaultPostProcess.vertex",
            "Shader/AdaptiveBrightnessDownsampleFinal.fragment")
        self.finalDownsamplePass.setShader(fpShader)

    def setShaderInput(self, name, value, *args):
        self.downscalePass0.setShaderInput(name, value, *args)
        self.finalDownsamplePass.setShaderInput(name, value, *args)

    def getOutputs(self):
        return {
        }
