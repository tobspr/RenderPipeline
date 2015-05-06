

from panda3d.core import Shader

from Code.Globals import Globals
from Code.RenderPass import RenderPass
from Code.RenderTarget import RenderTarget

class InitialRenderPass(RenderPass):

    """ This pass just fetches some render inputs and makes them available for
    the default rendering pass """

    def __init__(self):
        RenderPass.__init__(self)
        self.scene = Globals.base.render

    def getID(self):
        return "InitialRenderPass"

    def getRequiredInputs(self):
        return {
            "lastMVP": "Variables.lastMVP",
            "numUpdates": "Variables.numShadowUpdates",
            "updateSources": "Variables.shadowUpdateSources",
            "shadowAtlas": "ShadowScenePass.atlas",
            "cameraPosition": "Variables.cameraPosition"
        }

    def setShaders(self):
        shader = Shader.load(Shader.SLGLSL, 
            "Shader/DefaultShaders/Opaque/vertex.glsl",
            "Shader/DefaultShaders/Opaque/fragment.glsl")
        self.scene.setShader(shader, 20)

    def create(self):
        pass

    def getOutputs(self):
        return {
            "SceneReadyState": 0
        }

    def setShaderInput(self, name, value):
        self.scene.setShaderInput(name, value)
