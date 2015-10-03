
from panda3d.core import LVecBase2i, PTAMat4, UnalignedLMatrix4f, TransformState
from panda3d.core import Mat4, CSYupRight, CSZupRight, PTAVecBase3f, Texture
from direct.showbase.ShowBase import ShowBase

from Util.DebugObject import DebugObject

from MountManager import MountManager
from PipelineSettings import PipelineSettings
from Globals import Globals
from StageManager import StageManager
from Lighting.LightManager import LightManager

from GUI.OnscreenDebugger import OnscreenDebugger


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
        self.settings.load_from_file(path)

    def getStageMgr(self):
        """ Returns a handle to the stage manager object """
        return self.stageMgr

    def addLight(self, light):
        """ Adds a new light """
        self.lightMgr.addLight(light)

    def create(self):
        """ This creates the pipeline, and setups all buffers. It also constructs
        the showbase """

        if not self.settings.is_file_loaded():
            self.warn("No settings file loaded! Using default settings")

        # Construct the showbase
        ShowBase.__init__(self.showbase)

        # Load the globals
        Globals.load(self.showbase)
        Globals.font = Globals.loader.loadFont("Data/Font/DebugFont.ttf")
        Globals.resolution = LVecBase2i(self.showbase.win.getXSize(), 
            self.showbase.win.getYSize())

        # Adjust the camera settings
        self._adjustCameraSettings()

        # Create the debugger
        self.debugger = OnscreenDebugger(self)

        # Create the stage manager
        self.stageMgr = StageManager(self)
        self._createCommonInputs()

        # Create the light manager
        self.lightMgr = LightManager(self)

        self.stageMgr.setup()
        self._createCommonDefines()
        self.reloadShaders()
        self._initBindings()


    def reloadShaders(self):
        """ Reloads all shaders """
        self.stageMgr.set_shaders()
        self.lightMgr.reloadShaders()

    
    def _initBindings(self):
        """ Inits the tasks and keybindings """
        self.showbase.accept("r", self.reloadShaders)
        self.showbase.addTask(self._preRenderUpdate, "RP_BeforeRender", sort=10)
        self.showbase.addTask(self._postRenderUpdate, "RP_AfterRender", sort=100)

    
    def _preRenderUpdate(self, task):
        """ Update task which gets called before the update """
        self._updateCommonInputs()
        self.stageMgr.update_stages()
        self.lightMgr.update()
        return task.cont

    
    def _postRenderUpdate(self, task):
        """ Update task which gets called after the update """
        return task.cont

    
    def _createCommonDefines(self):
        """ Creates commonly used defines for the shader auto config """
        define = self.stageMgr.define

        # 3D viewport size
        define("WINDOW_WIDTH", Globals.resolution.x)
        define("WINDOW_HEIGHT", Globals.resolution.y)

        # Pass camera near and far plane
        define("CAMERA_NEAR", round(Globals.base.camLens.getNear(), 5))
        define("CAMERA_FAR", round(Globals.base.camLens.getFar(), 5))

        self.lightMgr.initDefines()

    
    def _createCommonInputs(self):
        """ Creates commonly used inputs """

        self.ptaCameraPos = PTAVecBase3f.emptyArray(1)

        self.stageMgr.add_input("mainCam", self.showbase.cam)
        self.stageMgr.add_input("mainRender", self.showbase.render)
        self.stageMgr.add_input("cameraPosition", self.ptaCameraPos)

        self.ptaCurrentViewMat = PTAMat4.emptyArray(1)
        self.stageMgr.add_input("currentViewMat", self.ptaCurrentViewMat)

        self.coordinateConverter = TransformState.makeMat(Mat4.convertMat(CSYupRight, CSZupRight))

        self._loadCommonTextures()

    
    def _loadCommonTextures(self):
        """ Loads commonly used textures """

        quantTex = loader.loadTexture("Data/NormalQuantization/NormalQuantizationTex-#.png", readMipmaps=True)
        quantTex.setMinfilter(Texture.FTLinearMipmapLinear)
        quantTex.setMagfilter(Texture.FTLinear)
        quantTex.setWrapU(Texture.WMRepeat)
        quantTex.setWrapV(Texture.WMRepeat)
        quantTex.setFormat(Texture.FRgba16)
        self.showbase.render.setShaderInput("NormalQuantizationTex", quantTex)


    
    def _updateCommonInputs(self):
        """ Updates the commonly used inputs """

        self.ptaCurrentViewMat[0] = UnalignedLMatrix4f(self.coordinateConverter.invertCompose(self.showbase.render.getTransform(self.showbase.cam)).getMat())
        self.ptaCameraPos[0] = base.camera.getPos(render)

    
    def _adjustCameraSettings(self):
        """ Sets the default camera settings """
        self.showbase.camLens.setNearFar(0.1, 70000)
        self.showbase.camLens.setFov(110)