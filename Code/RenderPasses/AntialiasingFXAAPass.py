
from panda3d.core import NodePath, Shader, LVecBase2i, Texture, PTAFloat, Vec4

from Code.Globals import Globals
from Code.RenderPass import RenderPass
from Code.RenderTarget import RenderTarget

class AntialiasingFXAAPass(RenderPass):

    """ This render pass takes the scene color texture as input and performs
    antialiasing. The result is an antialiased scene texture which can be
    processed further. 

    This pass uses FXAA 3.11 by nvidia."""

    def __init__(self):
        RenderPass.__init__(self)

    def getID(self):
        return "AntialiasingPass"

    def getRequiredInputs(self):
        return {
            "colorTex": ["TransparencyPass.resultTex", "LightingPass.resultTex"]
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

        return [shader]

    def getOutputs(self):
        return {
            "AntialiasingPass.resultTex": lambda: self.target.getColorTexture(),
        }

