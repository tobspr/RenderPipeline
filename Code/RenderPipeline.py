
import sys
import time

from panda3d.core import LVecBase2i, PTAMat4, UnalignedLMatrix4f, TransformState
from panda3d.core import Mat4, CSYupRight, CSZupRight, PTAVecBase3f, Texture
from panda3d.core import RenderState, BitMask32, load_prc_file, PandaSystem
from direct.showbase.ShowBase import ShowBase
from direct.stdpy.file import isfile

from .CommonResources import CommonResources
from .Globals import Globals
from .RenderTarget import RenderTarget

from .Util.DebugObject import DebugObject
from .Util.SettingsLoader import SettingsLoader
from .Util.NetworkUpdateListener import NetworkUpdateListener

from .GUI.OnscreenDebugger import OnscreenDebugger
from .GUI.PipelineLoadingScreen import PipelineLoadingScreen, EmptyLoadingScreen

from .Effects.EffectLoader import EffectLoader

from .PluginInterface.PluginManager import PluginManager
from .DayTime.DayTimeManager import DayTimeManager

from .Managers.MountManager import MountManager
from .Managers.StageManager import StageManager
from .Managers.LightManager import LightManager
from .Managers.TagStateManager import TagStateManager
from .Managers.IESProfileManager import IESProfileManager

class RenderPipeline(DebugObject):

    """ This is the main pipeline logic, it combines all components of the pipeline
    to form a working system. It does not do much work itself, but instead setups
    all the managers and systems to be able to do their work. """

    def __init__(self, showbase):
        """ Creates a new pipeline with a given showbase instance. This should be
        done before intializing the ShowBase, the pipeline will take care of that. """
        DebugObject.__init__(self, "RenderPipeline")
        self.debug("Starting pipeline, using Python", sys.version_info.major,
            "Architecture =", PandaSystem.getPlatform())
        self._showbase = showbase
        self._mount_manager = MountManager(self)
        self._settings = SettingsLoader(self, "Pipeline Settings")
        self._loading_screen = EmptyLoadingScreen()

    def get_mount_manager(self):
        """ Returns a handle to the mount manager. This can be used for setting
        the base path and also modifying the temp path. See the MountManager
        documentation for further information. """
        return self._mount_manager

    def set_loading_screen(self, loading_screen):
        """ Sets a loading screen to be used while loading the pipeline. When
        the pipeline gets constructed (and creates the showbase), create()
        will be called on the object. During the loading progress, 
        progress(msg) will be called. After the loading is finished,
        remove() will be called. If a custom loading screen is passed, those
        methods should be implemented. """
        self._loading_screen = loading_screen

    def set_default_loading_screen(self):
        """ Tells the pipeline to use the default loading screen. """
        self._loading_screen = PipelineLoadingScreen(self)

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

    def remove_light(self, light):
        """ Removes a previously attached light, check out the LightManager
        documentation for further information. """
        self._light_mgr.remove_light(light)

    def get_setting(self, setting_name):
        """ Returns a handle to the settings, returns an empty PipelineSettings
        object if no settings have been loaded so far. """
        return self._settings[setting_name]

    def create_default_skybox(self, size=40000):
        """ Returns the default skybox, with a scale of <size>, and all
        proper effects and shaders already applied. The skybox is already 
        parented to render as well. """
        skybox = self._com_resources.load_default_skybox()
        skybox.set_scale(size)
        skybox.reparent_to(Globals.render)
        self.set_effect(skybox, "Effects/Skybox.yaml", {"render_shadows": False}, 100)
        return skybox

    def get_plugin_mgr(self):
        """ Returns a handle to the plugin manager, this can be used to trigger
        hooks """
        return self._plugin_mgr

    def get_tag_mgr(self):
        """ Returns a handle to the tag state manager """
        return self._tag_mgr

    def get_daytime_mgr(self):
        """ Returns a handle to the DayTime manager """
        return self._daytime_mgr

    def load_ies_profile(self, filename):
        """ Loads an IES profile from a given filename and returns a handle which
        can be used to set an ies profile on a light """
        return self._ies_profile_mgr.load(filename)

    def set_effect(self, object, effect_src, options = None, sort = 30):
        """ Sets an effect to the given object, using the specified options.
        Check out the effect documentation for more information about possible
        options and configurations. The object should be a nodepath, and the
        effect will be applied to that nodepath and all nodepaths below whose
        current effect sort is less than the new effect sort (passed by the
        sort parameter). """

        effect = self._effect_loader.load_effect(effect_src, options)
        if not effect:
            return self.error("Could not apply effect")           

        # Apply default stage shader
        if not effect.get_option("render_gbuffer"):
            object.hide(TagStateManager.MASK_GBUFFER)
        else:
            object.set_shader(effect.get_shader_obj("GBuffer"), sort)
            object.show(TagStateManager.MASK_GBUFFER)
        
        # Apply shadow stage shader
        if not effect.get_option("render_shadows"):
            object.hide(TagStateManager.MASK_SHADOWS)
        else:
            shader = effect.get_shader_obj("Shadows")
            self._tag_mgr.apply_shadow_state(object, shader, str(effect.get_effect_id()), 25 + sort)
            object.show(TagStateManager.MASK_SHADOWS)

    def create(self):
        """ This creates the pipeline, and setups all buffers. It also constructs
        the showbase. The settings should have been loaded before calling this,
        and also the base and write path should have been initialized properly
        (see MountManager). """

        if not self._settings.is_file_loaded():
            return self.error("No settings file loaded! Please call load_settings.")

        # Check if the pipeline was properly installed
        if not isfile("Data/install.flag"):
            self.fatal("You didn't setup the pipeline yet! Please run setup.py.")

        # Load the default prc config
        load_prc_file("Config/configuration.prc")

        # Construct the showbase and init global variables
        ShowBase.__init__(self._showbase)
        self._init_globals()
    
        # Create the loading screen
        self._loading_screen.create()

        # Adjust the camera settings
        self._adjust_camera_settings()

        # Create the various managers and instances
        self._com_resources = CommonResources(self)
        self._tag_mgr = TagStateManager(self)
        self._plugin_mgr = PluginManager(self)
        self._debugger = OnscreenDebugger(self)
        self._effect_loader = EffectLoader()
        self._stage_mgr = StageManager(self)
        self._light_mgr = LightManager(self)
        self._daytime_mgr = DayTimeManager(self)
        self._ies_profile_mgr = IESProfileManager(self)

        # Load plugins and daytime settings
        self._plugin_mgr.load_plugins()
        self._daytime_mgr.load_settings()

        # Load common inputs and defines
        self._com_resources.load()
        self._create_common_defines()

        self._plugin_mgr.trigger_hook("on_stage_setup")

        # Setup the managers
        self._stage_mgr.setup()
        self._stage_mgr.set_shaders()
        self._light_mgr.reload_shaders()
        self._init_bindings()
        
        # Trigger the finish plugin hook
        self._plugin_mgr.trigger_hook("on_pipeline_created")

        # Set the default effect on render
        self.set_effect(Globals.render, "Effects/Default.yaml", {}, -10)

        # Hide the loading screen
        self._loading_screen.remove()

        self._start_listener()
        self.debug("Finished initialization.")

    def reload_shaders(self):
        """ Reloads all shaders """
        self.debug("Reloading shaders ..")
        self._debugger._error_msg_handler.clear_messages()
        self._debugger.set_reload_hint_visible(True)
        self._showbase.graphicsEngine.render_frame()
        self._showbase.graphicsEngine.render_frame()

        self._tag_mgr.cleanup_states()
        self._stage_mgr.set_shaders()
        self._light_mgr.reload_shaders()

        # Set the default effect on render and trigger the reload hook
        self.set_effect(Globals.render, "Effects/Default.yaml", {}, -10)
        self._plugin_mgr.trigger_hook("on_shader_reload")

        self._debugger.set_reload_hint_visible(False)

    def _init_globals(self):
        """ Inits all global bindings """
        Globals.load(self._showbase)
        Globals.resolution = LVecBase2i(
            self._showbase.win.get_x_size(),
            self._showbase.win.get_y_size())

        # Connect the render target output function to the debug object
        RenderTarget.RT_OUTPUT_FUNC = lambda *args: DebugObject.global_warn("RenderTarget", *args[1:])

    def _init_bindings(self):
        """ Inits the tasks and keybindings """
        self._showbase.accept("r", self.reload_shaders)
        self._showbase.addTask(self._manager_update_task, "RP_UpdateManagers", sort=10)
        self._showbase.addTask(self._plugin_pre_render_update, "RP_Plugin_BeforeRender", sort=12)
        self._showbase.addTask(self._plugin_post_render_update, "RP_Plugin_AfterRender", sort=1000)
        self._showbase.taskMgr.doMethodLater(0.5, self._clear_state_cache, "RP_ClearStateCache")

    def _clear_state_cache(self, task=None):
        """ Task which repeatedly clears the state cache to avoid storing
        unused states. """
        task.delayTime = 1.0
        TransformState.clear_cache()
        RenderState.clear_cache()
        return task.again

    def _start_listener(self):
        """ Starts a listener thread which listens for incoming connections to
        trigger a shader reload. This is used by the Plugin Configurator to dynamically
        update settings. """

        self._listener = NetworkUpdateListener(self)
        self._listener.setup()

    def _on_reload_trigger(self, msg):
        """ Internal method which gets called when a message arrived to the 
        listener """

        # Dont process the message directly, instead do that in the main thread,
        # after a short delay
        time.sleep(0.1)
        self._listener_update_queue.add(msg)

    def _manager_update_task(self, task):
        """ Update task which gets called before the rendering """
        self._listener.update()
        self._debugger.update()
        self._daytime_mgr.update()
        self._com_resources.update()
        self._stage_mgr.update_stages()
        self._light_mgr.update()
        return task.cont


    def _plugin_pre_render_update(self, task):
        """ Update task which gets called before the rendering, and updates the
        plugins. This is a seperate task to split the work, and be able to do
        better performance analysis """
        self._plugin_mgr.trigger_hook("pre_render_update")
        return task.cont

    def _plugin_post_render_update(self, task):
        """ Update task which gets called after the rendering """
        self._plugin_mgr.trigger_hook("post_render_update")
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
        self._plugin_mgr.init_defines()

    def _adjust_camera_settings(self):
        """ Sets the default camera settings """
        self._showbase.camLens.set_near_far(0.1, 70000)
        self._showbase.camLens.set_fov(90)
