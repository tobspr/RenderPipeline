
from ..Globals import Globals
from ..RenderPass import RenderPass
from ..RenderTarget import RenderTarget

from panda3d.core import Texture

class DeferredScenePass(RenderPass):

    """ This is the main scene pass which generates the G-Buffer used for 
    deferred rendering """

    def __init__(self):
        RenderPass.__init__(self)

    def getID(self):
        return "DeferredScenePass"

    def getRequiredInputs(self):
        return {
            "readyState": "SceneReadyState"
        }

    def create(self):
        self.target = RenderTarget("DeferredScenePass")
        self.target.addColorAndDepth()
        self.target.addAuxTextures(3)
        self.target.setAuxBits(16)
        self.target.setDepthBits(32)
        self.target.setCreateOverlayQuad(False)
        self.target.prepareSceneRender()
        self.target.setClearColor(False)
        self.target.setClearDepth(True)

    def getOutputs(self):
        return {
            "DeferredScenePass.wsNormal": lambda: self.target.getColorTexture(),
            "DeferredScenePass.velocity": lambda: self.target.getAuxTexture(0),

            "DeferredScenePass.depth": lambda: self.target.getDepthTexture(),
            "DeferredScenePass.data0": lambda: self.target.getColorTexture(),
            "DeferredScenePass.data1": lambda: self.target.getAuxTexture(0),
            "DeferredScenePass.data2": lambda: self.target.getAuxTexture(1),
            "DeferredScenePass.data3": lambda: self.target.getAuxTexture(2),
        }

    def setShaderInput(self, name, value):
        pass