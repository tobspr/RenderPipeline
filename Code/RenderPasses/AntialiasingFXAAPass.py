
from panda3d.core import NodePath, Shader, LVecBase2i, Texture, PTAFloat, Vec4

from Code.Globals import Globals
from Code.RenderPass import RenderPass
from Code.RenderTarget import RenderTarget

class AntialiasingFXAAPass(RenderPass):

    def __init__(self):
        RenderPass.__init__(self)

    def getID(self):
        return "AntialiasingPass"

    def getRequiredInputs(self):
        return {
            "colorTex": "LightingPass.resultTex"
        }

    def create(self):
        self.target = RenderTarget("Antialiasing FXAA")
        self.target.addColorTexture()
        self.target.prepareOffscreenBuffer()


    def setShaders(self):
        shader = Shader.load(Shader.SLGLSL, 
            "Shader/DefaultPostProcess.vertex",
            "Shader/Antialiasing/FXAA/FXAA3.fragment")
        self.target.setShader(shader)

    def getOutputs(self):
        return {
            "AntialiasingPass.resultTex": lambda: self.target.getColorTexture(),
        }

