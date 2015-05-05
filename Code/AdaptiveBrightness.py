

from panda3d.core import Shader, Texture, Vec4, PTAFloat

from RenderTarget import RenderTarget
from DebugObject import DebugObject
from Globals import Globals

class AdaptiveBrightness(DebugObject):

    """ This class handles the Adaptive Brightness feature, it downscales the
    Scene to get the average brightness and then slowly fades to the intended
    brightness """

    def __init__(self, pipeline):
        DebugObject.__init__(self, "AdaptiveBrightness")
        self.pipeline = pipeline

        self.targetExposure = PTAFloat.emptyArray(1)
        self.targetExposure[0] = 0.5
        self.adaptionSpeed = PTAFloat.emptyArray(1)
        self.adaptionSpeed[0] = 1.0

    def setupDownscalePass(self, size):
        """ Setups the downscale pass, which scales the scene to a 1x1 texture """
        self.size = size

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
        self.lastExposureStorage = Texture("Last Exposure")
        self.lastExposureStorage.setup2dTexture(1, 1, Texture.TFloat, Texture.FR32)
        self.lastExposureStorage.setClearColor(Vec4(self.targetExposure[0]))
        self.lastExposureStorage.clearImage()

        self.finalDownsamplePass.setShaderInput("lastExposureTex", self.lastExposureStorage)
        self.finalDownsamplePass.setShaderInput("dt", 0.0)

    def setTargetExposure(self, exposure):
        """ Sets the target exposure, where the scene will fade to """
        self.targetExposure[0] = exposure

    def setAdaptionSpeed(self, speed):
        """ Controls how fast the exposure is corrected """
        self.adaptionSpeed[0] = speed

    def setColorTex(self, colorTex):
        """ Sets the scene texture, which is required for the downscale pass """
        self.downscalePass0.setShaderInput("colorTex", colorTex)

    def getDownscaledTexture(self):
        """ Returns the 1x1 downscaled texture which contains the scene luminance """
        return self.finalDownsamplePass.getColorTexture()

    def update(self):
        """ Updates the brightness """
        self.finalDownsamplePass.setShaderInput("dt", Globals.clock.getDt())

    def reloadShader(self):
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