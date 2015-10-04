
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
        return self._stage_mgr

    def add_light(self, light):
        """ Adds a new light """
        self._light_mgr.add_light(light)

    def get_settings(self):
        """ Returns a handle to the settings"""
        return self._settings

    def create_default_skybox(self, size=40000):
        """ Returns the default skybox """
        skybox = Globals.loader.loadModel("Data/BuiltinModels/Skybox.egg.bam")
        skybox.set_scale(size)
        skybox.reparentTo(Globals.render)

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
        self._debugger = OnscreenDebugger(self)

        # Create the stage manager
        self._stage_mgr = StageManager(self)
        self._create_common_inputs()

        # Create the light manager
        self._light_mgr = LightManager(self)

        self._stage_mgr.setup()
        self._create_common_defines()
        self.reload_shaders()
        self._init_bindings()

    def reload_shaders(self):
        """ Reloads all shaders """
        self._stage_mgr.set_shaders()
        self._light_mgr.reload_shaders()

    def _init_bindings(self):
        """ Inits the tasks and keybindings """
        self._showbase.accept("r", self.reload_shaders)
        self._showbase.addTask(self._pre_render_update, "RP_BeforeRender", sort=10)
        self._showbase.addTask(self._post_render_update, "RP_AfterRender", sort=100)

    def _pre_render_update(self, task):
        """ Update task which gets called before the update """
        self._update_common_inputs()
        self._stage_mgr.update_stages()
        self._light_mgr.update()
        return task.cont

    def _post_render_update(self, task):
        """ Update task which gets called after the update """
        return task.cont

    def _create_common_defines(self):
        """ Creates commonly used defines for the shader auto config """
        define = self._stage_mgr.define

        # 3D viewport size
        define("WINDOW_WIDTH", Globals.resolution.x)
        define("WINDOW_HEIGHT", Globals.resolution.y)

        # Pass camera near and far plane
        define("CAMERA_NEAR", round(Globals.base.camLens.get_near(), 5))
        define("CAMERA_FAR", round(Globals.base.camLens.get_far(), 5))

        self._light_mgr.init_defines()

    def _create_common_inputs(self):
        """ Creates commonly used inputs """

        self._pta_camera_pos = PTAVecBase3f.empty_array(1)

        self._stage_mgr.add_input("mainCam", self._showbase.cam)
        self._stage_mgr.add_input("mainRender", self._showbase.render)
        self._stage_mgr.add_input("cameraPosition", self._pta_camera_pos)

        self._pta_current_view_mat = PTAMat4.empty_array(1)
        self._stage_mgr.add_input("currentViewMat", self._pta_current_view_mat)

        self._coordinate_converter = TransformState.make_mat(
            Mat4.convert_mat(CSYupRight, CSZupRight))

        self._load_common_textures()

    def _load_common_textures(self):
        """ Loads commonly used textures """

        # Load the normal quantization tex
        quant_tex = Globals.loader.loadTexture(
            "Data/NormalQuantization/NormalQuantizationTex-#.png",
            readMipmaps=True)
        quant_tex.set_minfilter(Texture.FTLinearMipmapLinear)
        quant_tex.set_magfilter(Texture.FTLinear)
        quant_tex.set_wrap_u(Texture.WMRepeat)
        quant_tex.set_wrap_v(Texture.WMRepeat)
        quant_tex.set_format(Texture.FRgba16)
        self._showbase.render.set_shader_input("NormalQuantizationTex", quant_tex)

        # Load the fallback cubemap
        self.debug("Loading environment cubemap")
        envmap = Globals.loader.loadCubeMap("Data/DefaultCubemap/Filtered/#-#.png", readMipmaps=True)
        envmap.set_minfilter(Texture.FTLinearMipmapLinear)
        envmap.set_magfilter(Texture.FTLinear)
        envmap.set_wrap_u(Texture.WMRepeat)
        envmap.set_wrap_v(Texture.WMRepeat)
        envmap.set_wrap_w(Texture.WMRepeat)
        self._stage_mgr.add_input("DefaultEnvmap", envmap)

    def _update_common_inputs(self):
        """ Updates the commonly used inputs """

        self._pta_current_view_mat[0] = UnalignedLMatrix4f(
            self._coordinate_converter.invert_compose(
                self._showbase.render.get_transform(self._showbase.cam)).get_mat())
        self._pta_camera_pos[0] = self._showbase.camera.get_pos(render)

    def _adjust_camera_settings(self):
        """ Sets the default camera settings """
        self._showbase.camLens.set_near_far(0.1, 70000)
        self._showbase.camLens.set_fov(110)
