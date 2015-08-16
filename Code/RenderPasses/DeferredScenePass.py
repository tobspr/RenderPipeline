
from panda3d.core import Camera

from ..Globals import Globals
from ..RenderPass import RenderPass
from ..RenderTarget import RenderTarget

from panda3d.core import Texture, NodePath, ColorWriteAttrib, DepthWriteAttrib
from panda3d.core import DepthTestAttrib, DepthOffsetAttrib, CullFaceAttrib
from panda3d.core import AlphaTestAttrib, TransparencyAttrib, Vec4

class DeferredScenePass(RenderPass):

    """ This is the main scene pass which generates the G-Buffer used for 
    deferred rendering """

    def __init__(self, pipeline):
        RenderPass.__init__(self)
        self.pipeline = pipeline

    def getID(self):
        return "DeferredScenePass"

    def getRequiredInputs(self):
        return {
            "readyState": "SceneReadyState"
        }

    def create(self):

        earlyZ = self.pipeline.settings.enableEarlyZ

        if earlyZ:
            self.prepassCam = Camera(Globals.base.camNode)
            self.prepassCam.setTagStateKey("EarlyZShader")
            self.prepassCam.setName("EarlyZCamera")
            self.prepassCamNode = Globals.base.camera.attachNewNode(self.prepassCam)
            Globals.render.setTag("EarlyZShader", "Default")
        else:
            self.prepassCam = None

        # modify default camera initial state
        initial = Globals.base.camNode.getInitialState()
        initialNode = NodePath("IntiialState")
        initialNode.setState(initial)
        
        if earlyZ:
            initialNode.setAttrib(DepthWriteAttrib.make(DepthWriteAttrib.MOff))
            initialNode.setAttrib(DepthTestAttrib.make(DepthTestAttrib.MEqual))
            pass
        else:
            initialNode.setAttrib(DepthTestAttrib.make(DepthTestAttrib.MLessEqual))

        # initialNode.setAttrib(ColorWriteAttrib.make(ColorWriteAttrib.COff), 10000)
        # initialNode.setAttrib(CullFaceAttrib.make(CullFaceAttrib.MCullClockwise), 10000)
        Globals.base.camNode.setInitialState(initialNode.getState())

        self.target = RenderTarget("DeferredScenePass")
        self.target.addColorAndDepth()
        self.target.addAuxTextures(3)
        self.target.setAuxBits(16)
        self.target.setDepthBits(32)
        self.target.setCreateOverlayQuad(False)
        
        if earlyZ:
            self.target.prepareSceneRender(earlyZ=True, earlyZCam=self.prepassCamNode)
        else:
            self.target.prepareSceneRender()

        self.target.setClearColor(True, color=Vec4(1, 1, 0, 1))

        if earlyZ:
            self.target.setClearDepth(False)
        else:
            self.target.setClearDepth(True)


    def registerEarlyZTagState(self, name, state):
        """ Registers a new tag state """
        if not self.prepassCam:
            return

        # state.setAttrib(CullFaceAttrib.make(CullFaceAttrib.MCullClockwise), 10000)
        state.setAttrib(ColorWriteAttrib.make(ColorWriteAttrib.COff), 10000)
        state.setAttrib(AlphaTestAttrib.make(AlphaTestAttrib.MNone, 1.0), 10000)
        state.setAttrib(DepthWriteAttrib.make(DepthWriteAttrib.MOn), 10000)
        state.setAttrib(DepthTestAttrib.make(DepthTestAttrib.MLess), 10000)
        state.setAttrib(TransparencyAttrib.make(TransparencyAttrib.MNone), 10000)

        self.prepassCam.setTagState(name, state.getState()) 

    def setShaders(self):
        self.registerEarlyZTagState("Default", NodePath("DefaultEarlyZPass"))
        return []

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