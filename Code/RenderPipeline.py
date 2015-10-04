
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
        self._showbase = showbase
        self._mount_manager = MountManager(self)
        self._settings = PipelineSettings(self)

    def get_mount_manager(self):
        """ Returns a handle to the mount manager """
        return self._mount_manager

    def load_settings(self, path):
        """ Loads the pipeline configuration from a given filename. If you call
        this more than once, only the settings of the last file will be used """
        self._settings.load_from_file(path)

    def get_stage_mgr(self):
        """ Returns a handle to the stage manager object """
        return self.stage_mgr

    def add_light(self, light):
        """ Adds a new light """
        self.light_mgr.add_light(light)

    def get_settings(self):
        """ Returns a handle to the settings"""
        return self._settings

    def create(self):
        """ This creates the pipeline, and setups all buffers. It also constructs
        the showbase """

        if not self._settings.is_file_loaded():
            self.warn("No settings file loaded! Using default settings")

        # Construct the showbase
        ShowBase.__init__(self._showbase)

        # Load the globals
        Globals.load(self._showbase)
        Globals.font = Globals.loader.loadFont("Data/Font/DebugFont.ttf")
        Globals.resolution = LVecBase2i(self._showbase.win.get_x_size(),
            self._showbase.win.get_y_size())

        # Adjust the camera settings
        self._adjust_camera_settings()

        # Create the debugger
        self.debugger = OnscreenDebugger(self)

        # Create the stage manager
        self.stage_mgr = StageManager(self)
        self._create_common_inputs()

        # Create the light manager
        self.light_mgr = LightManager(self)

        self.stage_mgr.setup()
        self._create_common_defines()
        self.reload_shaders()
        self._init_bindings()

    def reload_shaders(self):
        """ Reloads all shaders """
        self.stage_mgr.set_shaders()
        self.light_mgr.reload_shaders()

    def _init_bindings(self):
        """ Inits the tasks and keybindings """
        self._showbase.accept("r", self.reload_shaders)
        self._showbase.addTask(self._pre_render_update, "RP_BeforeRender", sort=10)
        self._showbase.addTask(self._post_render_update, "RP_AfterRender", sort=100)

    def _pre_render_update(self, task):
        """ Update task which gets called before the update """
        self._update_common_inputs()
        self.stage_mgr.update_stages()
        self.light_mgr.update()
        return task.cont

    def _post_render_update(self, task):
        """ Update task which gets called after the update """
        return task.cont

    def _create_common_defines(self):
        """ Creates commonly used defines for the shader auto config """
        define = self.stage_mgr.define

        # 3D viewport size
        define("WINDOW_WIDTH", Globals.resolution.x)
        define("WINDOW_HEIGHT", Globals.resolution.y)

        # Pass camera near and far plane
        define("CAMERA_NEAR", round(Globals.base.camLens.get_near(), 5))
        define("CAMERA_FAR", round(Globals.base.camLens.get_far(), 5))

        self.light_mgr.init_defines()

    def _create_common_inputs(self):
        """ Creates commonly used inputs """

        self.pta_camera_pos = PTAVecBase3f.empty_array(1)

        self.stage_mgr.add_input("mainCam", self._showbase.cam)
        self.stage_mgr.add_input("mainRender", self._showbase.render)
        self.stage_mgr.add_input("cameraPosition", self.pta_camera_pos)

        self.pta_current_view_mat = PTAMat4.empty_array(1)
        self.stage_mgr.add_input("currentViewMat", self.pta_current_view_mat)

        self.coordinate_converter = TransformState.make_mat(
            Mat4.convert_mat(CSYupRight, CSZupRight))

        self._load_common_textures()

    def _load_common_textures(self):
        """ Loads commonly used textures """

        quant_tex = Globals.loader.loadTexture(
            "Data/NormalQuantization/NormalQuantizationTex-#.png",
            readMipmaps=True)
        quant_tex.set_minfilter(Texture.FTLinearMipmapLinear)
        quant_tex.set_magfilter(Texture.FTLinear)
        quant_tex.set_wrap_u(Texture.WMRepeat)
        quant_tex.set_wrap_v(Texture.WMRepeat)
        quant_tex.set_format(Texture.FRgba16)
        self._showbase.render.set_shader_input("NormalQuantizationTex", quant_tex)

    def _update_common_inputs(self):
        """ Updates the commonly used inputs """

        self.pta_current_view_mat[0] = UnalignedLMatrix4f(
            self.coordinate_converter.invert_compose(
                self._showbase.render.get_transform(self._showbase.cam)).get_mat())
        self.pta_camera_pos[0] = self._showbase.camera.get_pos(render)

    def _adjust_camera_settings(self):
        """ Sets the default camera settings """
        self._showbase.camLens.set_near_far(0.1, 70000)
        self._showbase.camLens.set_fov(110)
