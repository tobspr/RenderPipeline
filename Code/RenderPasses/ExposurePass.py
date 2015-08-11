
from panda3d.core import Shader

from ..Globals import Globals
from ..RenderPass import RenderPass
from ..RenderTarget import RenderTarget

class ExposurePass(RenderPass):

    """ This pass applies srgb and the (dynamic) exposure to the rendered image, and
    also does the color correction """

    def __init__(self):
        RenderPass.__init__(self)

    def getID(self):
        return "ExposurePass"

    def getRequiredInputs(self):
        return {
            "sceneTex": ["SSLRPass.resultTex", "TransparencyPass.resultTex", "LightingPass.resultTex"],
        }

    def setShaders(self):
        shader = Shader.load(Shader.SLGLSL, 
            "Shader/DefaultPostProcess.vertex",
            "Shader/ExposurePass.fragment")
        self.target.setShader(shader)

        return [shader]

    def create(self):
        self.target = RenderTarget("ExposurePass")
        self.target.addColorTexture()
        self.target.setColorBits(16)
        self.target.prepareOffscreenBuffer()

    def getOutputs(self):
        return {
            "ExposurePass.resultTex": lambda: self.target.getColorTexture(),
        }

