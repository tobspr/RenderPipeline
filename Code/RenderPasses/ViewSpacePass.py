
from panda3d.core import NodePath, Shader, LVecBase2i, Texture, GeomEnums

from ..Globals import Globals
from ..RenderPass import RenderPass
from ..RenderTarget import RenderTarget

class ViewSpacePass(RenderPass):

    """ This pass is created when any pass in the pipeline requires view space
    normals or positions. It takes the scene depth as input and computes the
    view space position and normal from that """

    def __init__(self):
        RenderPass.__init__(self)

    def getID(self):
        return "ViewSpacePass"

    def getRequiredInputs(self):
        return {
            "positionTex": "DeferredScenePass.wsPosition",
            "depthTex": "DeferredScenePass.depth",
            "mainRender": "Variables.mainRender",
            "mainCam": "Variables.mainCam",
            "currentViewMat": "Variables.currentViewMat"
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

        return [shader]

    def getOutputs(self):
        return {
            "ViewSpacePass.normals": lambda: self.target.getColorTexture(),
            "ViewSpacePass.position": lambda: self.target.getAuxTexture(0),
        }
