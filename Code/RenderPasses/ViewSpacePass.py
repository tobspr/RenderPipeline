
from panda3d.core import NodePath, Shader, LVecBase2i, Texture, GeomEnums

from Code.Globals import Globals
from Code.RenderPass import RenderPass
from Code.RenderTarget import RenderTarget

class ViewSpacePass(RenderPass):

    def __init__(self):
        RenderPass.__init__(self)

    def getID(self):
        return "ViewSpacePass"

    def getRequiredInputs(self):
        return {
            "positionTex": "DeferredScenePass.wsPosition",
            "depthTex": "DeferredScenePass.depth",
            "mainRender": "Variables.mainRender",
            "mainCam": "Variables.mainCam"
        }

    def create(self):
        self.target = RenderTarget("ViewSpacePass")
        self.target.addColorTexture()
        self.target.addAuxTexture()
        self.target.setColorBits(16)
        self.target.setAuxBits(16)
        self.target.prepareOffscreenBuffer()
 
    def setShaders(self):
        shader = Shader.load(Shader.SLGLSL, 
            "Shader/DefaultPostProcess.vertex",
            "Shader/ViewSpacePass.fragment")
        self.target.setShader(shader)

    def getOutputs(self):
        return {
            "ViewSpacePass.normals": lambda: self.target.getColorTexture(),
            "ViewSpacePass.position": lambda: self.target.getAuxTexture(0),
        }

    def setShaderInput(self, name, value):
        self.target.setShaderInput(name, value)
