
from panda3d.core import LVecBase2i, PTAMat4, UnalignedLMatrix4f, TransformState
from panda3d.core import Mat4, CSYupRight, CSZupRight
from direct.showbase.ShowBase import ShowBase

from Util.DebugObject import DebugObject
from Util.FunctionDecorators import protected

from MountManager import MountManager
from PipelineSettings import PipelineSettings
from Globals import Globals
from StageManager import StageManager
from Lighting.LightManager import LightManager

from GUI.OnscreenDebugger import OnscreenDebugger

from Stages.EarlyZStage import EarlyZStage

class RenderPipeline(DebugObject):

    """ This is the main pipeline logic, it combines all components of the pipeline
    to form a working system """

    def __init__(self, showbase):
        """ Creates a new pipeline with a given showbase instance. This should be
        done *before* intializing the ShowBase (with ShowBase.__init__(self)) """

        DebugObject.__init__(self, "RenderPipeline")
        self.debug("Starting pipeline ..")
        self.showbase = showbase
        self.mountManager = MountManager(self)
        self.settings = PipelineSettings(self)

    def getMountManager(self):
        """ Returns a handle to the mount manager """
        return self.mountManager

    def loadSettings(self, path):
        """ Loads the pipeline configuration from a given filename. If you call
        this more than once, only the settings of the last file will be used """
        self.settings.loadFromFile(path)

    def getStageMgr(self):
        """ Returns a handle to the stage manager object """
        return self.stageMgr

    def addLight(self, light):
        """ Adds a new light """
        self.lightMgr.addLight(light)

    def create(self):
        """ This creates the pipeline, and setups all buffers. It also constructs
        the showbase """

        if not self.settings.isFileLoaded():
            self.warn("No settings file loaded! Using default settings")

        # Construct the showbase
        ShowBase.__init__(self.showbase)

        # Load the globals
        Globals.load(self.showbase)
        Globals.font = Globals.loader.loadFont("Data/Font/DebugFont.ttf")
        Globals.resolution = LVecBase2i(self.showbase.win.getXSize(), self.showbase.win.getYSize())

        # Adjust the camera settings
        self._adjustCameraSettings()

        # Create the debugger
        self.debugger = OnscreenDebugger(self)

        # Create the stage manager
        self.stageMgr = StageManager(self)
        self._createCommonInputs()

        # Create the light manager
        self.lightMgr = LightManager(self)

        self.stageMgr.addStage(EarlyZStage(self))
        self.stageMgr.setup()
        self._createCommonDefines()


        self.reloadShaders()


        self.initBindings()

    def initBindings(self):
        """ Inits the tasks and keybindings """
        self.showbase.accept("r", self.reloadShaders)
        self.showbase.addTask(self._preRenderUpdate, "RP_BeforeRender", sort=10)
        self.showbase.addTask(self._postRenderUpdate, "RP_AfterRender", sort=100)

    def reloadShaders(self):
        """ Reloads all shaders """
        self.stageMgr.setShaders()
        self.lightMgr.reloadShaders()

    @protected
    def _preRenderUpdate(self, task):
        """ Update task which gets called before the update """
        self._updateCommonInputs()
        self.stageMgr.updateStages()
        self.lightMgr.update()
        return task.cont

    @protected
    def _postRenderUpdate(self, task):
        """ Update task which gets called after the update """
        return task.cont

    @protected
    def _createCommonDefines(self):
        """ Creates commonly used defines for the shader auto config """
        define = self.stageMgr.define

        # 3D viewport size
        define("WINDOW_WIDTH", Globals.resolution.x)
        define("WINDOW_HEIGHT", Globals.resolution.y)

        # Pass camera near and far plane
        define("CAMERA_NEAR", round(Globals.base.camLens.getNear(), 3))
        define("CAMERA_FAR", round(Globals.base.camLens.getFar(), 3))

        self.lightMgr.initDefines()

    @protected
    def _createCommonInputs(self):
        """ Creates commonly used inputs """

        self.stageMgr.addInput("mainCam", self.showbase.cam)
        self.stageMgr.addInput("mainRender", self.showbase.render)

        self.ptaCurrentViewMat = PTAMat4.emptyArray(1)
        self.stageMgr.addInput("currentViewMat", self.ptaCurrentViewMat)

        self.coordinateConverter = TransformState.makeMat(Mat4.convertMat(CSYupRight, CSZupRight))

    @protected
    def _updateCommonInputs(self):
        """ Updates the commonly used inputs """

        self.ptaCurrentViewMat[0] = UnalignedLMatrix4f(
            self.coordinateConverter.invertCompose(self.showbase.render.getTransform(self.showbase.cam)).getMat())

    @protected
    def _adjustCameraSettings(self):
        """ Sets the default camera settings """
        self.showbase.camLens.setNearFar(0.1, 70000)
        self.showbase.camLens.setFov(110)