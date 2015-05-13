
from panda3d.core import NodePath, Shader, LVecBase2i, Texture, PTAFloat, Vec4

from Code.Globals import Globals
from Code.RenderPass import RenderPass
from Code.RenderTarget import RenderTarget

class DynamicExposurePass(RenderPass):

    """ This pass handles the dynamic exposure feature, it downscales the
    Scene to get the average brightness and then outputs a new exposure which
    can be used by the lighting pass. """

    def __init__(self, pipeline):
        RenderPass.__init__(self)
        self.pipeline = pipeline

        # Create the storage for the exposure. We cannot simply use the color output
        # as the RenderTargetMatcher would have problems with that (Circular Reference)
        self.lastExposureStorage = Texture("Last Exposure")
        self.lastExposureStorage.setup2dTexture(1, 1, Texture.TFloat, Texture.FR32)

        # Registers the texture so the lighting pass can use it
        self.pipeline.renderPassManager.registerStaticVariable(
            "dynamicExposureTex", self.lastExposureStorage)


    def getID(self):
        return "DynamicExposurePass"

    def getRequiredInputs(self):
        return {
            "colorTex": "LightingPass.resultTex",
            "dt": "Variables.frameDelta"
        }

    def create(self):

        # Fetch the original texture size from the window size
        size = LVecBase2i(Globals.base.win.getXSize(), Globals.base.win.getYSize())

        # Create the first downscale pass which reads the scene texture, does a 
        # 2x2 inplace box filter, and then converts the result to luminance. 
        # Using luminance allows faster downscaling, as we can use texelGather then
        self.downscalePass0 = RenderTarget("Downscale Initial")
        self.downscalePass0.addColorTexture()
        self.downscalePass0.setSize(size.x / 2, size.y / 2)
        self.downscalePass0.prepareOffscreenBuffer()

        # Store the current size of the pass
        workSizeX, workSizeY = int(size.x / 2), int(size.y / 2)

        self.downscalePasses = []
        passIdx = 0
        lastTex = self.downscalePass0.getColorTexture()

        # Scale the scene until there are only a few pixels left. Each pass does a 
        # 4x4 inplace box filter, which is cheap because we can sample the luminance
        # only.
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

        # Create the final pass which computes the average of all left pixels,
        # compares that with the last exposure and stores the difference.
        self.finalDownsamplePass = RenderTarget("Downscale Final")
        self.finalDownsamplePass.setSize(1, 1)
        # self.finalDownsamplePass.setColorBits(16)
        # self.finalDownsamplePass.addColorTexture()
        self.finalDownsamplePass.setColorWrite(False)
        self.finalDownsamplePass.prepareOffscreenBuffer()
        self.finalDownsamplePass.setShaderInput("luminanceTex", lastTex)
        self.finalDownsamplePass.setShaderInput("targetExposure", 
            self.pipeline.settings.targetExposure)
        self.finalDownsamplePass.setShaderInput("adaptionSpeed", 
            self.pipeline.settings.brightnessAdaptionSpeed)

        # Clear the storage in the beginning
        self.lastExposureStorage.setClearColor(Vec4(0))
        self.lastExposureStorage.clearImage()

        # Set defines and other inputs
        self.finalDownsamplePass.setShaderInput("lastExposureTex", self.lastExposureStorage)
        self.pipeline.renderPassManager.registerDefine("USE_DYNAMIC_EXPOSURE", 1)

    def setShaders(self):
        shaderFirstPass = Shader.load(Shader.SLGLSL, 
            "Shader/DefaultPostProcess.vertex",
            "Shader/AdaptiveBrightnessFirstPass.fragment")
        self.downscalePass0.setShader(shaderFirstPass)

        shaderDownsample = Shader.load(Shader.SLGLSL, 
            "Shader/DefaultPostProcess.vertex",
            "Shader/AdaptiveBrightnessDownsample.fragment")
        for scalePass in self.downscalePasses:
            scalePass.setShader(shaderDownsample)

        shaderFinal = Shader.load(Shader.SLGLSL, 
            "Shader/DefaultPostProcess.vertex",
            "Shader/AdaptiveBrightnessDownsampleFinal.fragment")
        self.finalDownsamplePass.setShader(shaderFinal)

        return [shaderFirstPass, shaderDownsample, shaderFinal]

    def setShaderInput(self, name, value, *args):
        self.downscalePass0.setShaderInput(name, value, *args)
        self.finalDownsamplePass.setShaderInput(name, value, *args)

    def getOutputs(self):
        return {
        }
