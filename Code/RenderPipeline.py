
from panda3d.core import LVecBase2i, PTAMat4, UnalignedLMatrix4f, TransformState
from panda3d.core import Mat4, CSYupRight, CSZupRight, PTAVecBase3f, Texture
from direct.showbase.ShowBase import ShowBase

from Util.DebugObject import DebugObject

from MountManager import MountManager
from PipelineSettings import PipelineSettings
from Globals import Globals
from StageManager import StageManager
from Lighting.LightManager import LightManager
from Effects.EffectLoader import EffectLoader

from GUI.OnscreenDebugger import OnscreenDebugger


class RenderPipeline(DebugObject):

    """ This is the main pipeline logic, it combines all components of the pipeline
    to form a working system """

    def __init__(self, showbase):
        """ Creates a new pipeline with a given showbase instance. This should be
        done before intializing the ShowBase, the pipeline will take care of that. """
        DebugObject.__init__(self, "RenderPipeline")
        self.debug("Starting pipeline ..")
        self._showbase = showbase
        self._mount_manager = MountManager(self)
        self._settings = PipelineSettings(self)

    def get_mount_manager(self):
        """ Returns a handle to the mount manager. This can be used for setting
        the base path and also modifying the temp path. See the MountManager
        documentation for further information. """
        return self._mount_manager

    def load_settings(self, path):
        """ Loads the pipeline configuration from a given filename. Usually this
        is the 'Config/pipeline.ini' file. If you call this more than once,
        only the settings of the last file will be used. """
        self._settings.load_from_file(path)

    def get_stage_mgr(self):
        """ Returns a handle to the stage manager object, this function is only
        internally used, but public so other classes can access this. Not indented
        for use by the user! """
        return self._stage_mgr

    def add_light(self, light):
        """ Adds a new light to the rendered lights, check out the LightManager
        documentation for further information. """
        self._light_mgr.add_light(light)

    def get_settings(self):
        """ Returns a handle to the settings, returns an empty PipelineSettings
        object if no settings have been loaded so far. """
        return self._settings

    def create_default_skybox(self, size=40000):
        """ Returns the default skybox, with a scale of <size>, and all
        proper effects and shaders already applied. The skybox is already 
        parented to render aswell. """
        skybox = Globals.loader.loadModel("Data/BuiltinModels/Skybox.egg.bam")
        skybox.set_scale(size)
        skybox.reparentTo(Globals.render)
        self.set_effect(skybox, "Effects/Skybox.yaml", 
                        {"cast_shadows": False}, 100)
        return skybox

    def set_effect(self, object, effect_src, options = None, sort = 30):
        """ Sets an effect to the given object, using the specified options.
        Check out the effect documentation for more information about possible
        options and configurations. The object should be a nodepath, and the
        effect will be applied to that nodepath and all nodepaths below whose
        current effect sort is less than the new effect sort (passed by the
        sort parameter). """

        effect_handle = self._effect_loader.load_effect(effect_src, options)
        if not effect_handle:
            self.error("Could not apply effect")           

        # Apply default stage shader
        object.set_shader(effect_handle.get_shader_obj("GBuffer"), sort)

        # TODO: Apply the shader from different stages


    def create(self):
        """ This creates the pipeline, and setups all buffers. It also constructs
        the showbase. The settings should have been loaded before calling this,
        and also the base and write path should have been initialized properly
        (see MountManager). """

        if not self._settings.is_file_loaded():
            self.warn("No settings file loaded! Using default settings")

        # Construct the showbase
        ShowBase.__init__(self._showbase)

        # Load the globals
        Globals.load(self._showbase)
        Globals.resolution = LVecBase2i(
            self._showbase.win.get_x_size(),
            self._showbase.win.get_y_size())
        self._load_default_font()

        # Adjust the camera settings
        self._adjust_camera_settings()

        # Create the various managers and instances
        self._debugger = OnscreenDebugger(self)
        self._effect_loader = EffectLoader()
        self._stage_mgr = StageManager(self)
        self._light_mgr = LightManager(self)

        # Setup common inputs and defines
        self._create_common_inputs()
        self._create_common_defines()

        # Setup the managers
        self._stage_mgr.setup()
        self.reload_shaders()
        self._init_bindings()
        
        # Set the default effect on render
        self.set_effect(Globals.render, "Effects/Default.yaml", {}, -10)

    def reload_shaders(self):
        """ Reloads all shaders """
        self._stage_mgr.set_shaders()
        self._light_mgr.reload_shaders()

    def _load_default_font(self):
        """ Loads the default font used for rendering and assigns it to 
        Globals.font for further usage """
        Globals.font = Globals.loader.loadFont("Data/Font/Roboto-Light.ttf")
        # Globals.font = Globals.loader.loadFont("Data/Font/DebugFont.ttf")
        Globals.font.set_pixels_per_unit(25)
        Globals.font.set_poly_margin(0.0)
        Globals.font.set_texture_margin(1)
        
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
        self._pta_current_view_proj_mat = PTAMat4.empty_array(1)

        self._stage_mgr.add_input("mainCam", self._showbase.cam)
        self._stage_mgr.add_input("mainRender", self._showbase.render)
        self._stage_mgr.add_input("cameraPosition", self._pta_camera_pos)
        self._stage_mgr.add_input("currentViewProjMat", self._pta_current_view_proj_mat)

        self._pta_view_mat_zup = PTAMat4.empty_array(1)
        self._stage_mgr.add_input("currentViewMatZup", self._pta_view_mat_zup)

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

        view_transform = self._showbase.render.get_transform(self._showbase.cam)
        self._pta_view_mat_zup[0] = (
            self._coordinate_converter.invert_compose(view_transform).get_mat())
        self._pta_camera_pos[0] = self._showbase.camera.get_pos(render)

        self._pta_current_view_proj_mat[0] = view_transform.get_mat() *\
            self._showbase.camLens.get_projection_mat()

    def _adjust_camera_settings(self):
        """ Sets the default camera settings """
        self._showbase.camLens.set_near_far(0.1, 70000)
        self._showbase.camLens.set_fov(110)
