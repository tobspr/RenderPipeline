"""

RenderPipeline

Copyright (c) 2014-2016 tobspr <tobias.springer1@gmail.com>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
 	 	    	 	
"""

import sys
import time

from panda3d.core import LVecBase2i, TransformState, RenderState, load_prc_file
from panda3d.core import PandaSystem
from direct.showbase.ShowBase import ShowBase
from direct.stdpy.file import isfile, open

from .Globals import Globals
from .PipelineExtensions import PipelineExtensions
from .CommonResources import CommonResources
from .CommonStages import CommonStages
from .Native import TagStateManager
from .RenderTarget import RenderTarget

from .Util.DebugObject import DebugObject
from .Util.SettingsLoader import SettingsLoader
from .Util.NetworkUpdateListener import NetworkUpdateListener
from .GUI.OnscreenDebugger import OnscreenDebugger
from .Effects.EffectLoader import EffectLoader
from .PluginInterface.PluginManager import PluginManager
from .DayTime.DayTimeManager import DayTimeManager

from .Managers.MountManager import MountManager
from .Managers.StageManager import StageManager
from .Managers.LightManager import LightManager
from .Managers.IESProfileManager import IESProfileManager

class RenderPipeline(PipelineExtensions, DebugObject):

    """ This is the main pipeline logic, it combines all components of the
    pipeline to form a working system. It does not do much work itself, but
    instead setups all the managers and systems to be able to do their work.

    It also derives from RPExtensions to provide some useful functions like
    creating a default skybox or loading effect files. """

    def __init__(self, showbase):
        """ Creates a new pipeline with a given showbase instance. This should
        be done before intializing the ShowBase, the pipeline will take care of
        that. """
        DebugObject.__init__(self, "RenderPipeline")
        self.debug("Using Python {} with architecture {}".format(
            sys.version_info.major, PandaSystem.get_platform()))
        self._showbase = showbase
        self._mount_mgr = MountManager(self)
        self._settings = SettingsLoader(self, "Pipeline Settings")
        self.set_default_loading_screen()

        # Check for the right Panda3D version
        if not self._check_version():
            self.fatal("Your Panda3D version is too old! Please update to a newer "
                       " version! (You need a development version of panda).")

    def load_settings(self, path):
        """ Loads the pipeline configuration from a given filename. Usually
        this is the 'Config/pipeline.ini' file. If you call this more than once,
        only the settings of the last file will be used. """
        self._settings.load_from_file(path)

    def get_setting(self, setting_name):
        """ Returns a handle to the settings, returns an empty PipelineSettings
        object if no settings have been loaded so far. """
        return self._settings[setting_name]

    def reload_shaders(self):
        """ Reloads all shaders """
        self.debug("Reloading shaders ..")
        self._debugger.get_error_msg_handler().clear_messages()
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

    def create(self):
        """ This creates the pipeline, and setups all buffers. It also
        constructs the showbase. The settings should have been loaded before
        calling this, and also the base and write path should have been
        initialized properly (see MountManager). """

        start_time = time.time()

        if not self._mount_mgr.is_mounted:
            self.debug("Mount manager was not mounted, mounting now ...")
            self._mount_mgr.mount()

        if not self._settings.is_file_loaded():
            self.debug("No settings loaded, loading from default location")
            self._settings.load_from_file("$$Config/pipeline.yaml")

        # Check if the pipeline was properly installed, before including anything else
        if not isfile("Data/install.flag"):
            DebugObject.global_error(
                "CORE", "You didn't setup the pipeline yet! Please run setup.py.")
            sys.exit(1)

        # Load the default prc config
        load_prc_file("$$Config/configuration.prc")

        # Construct the showbase and init global variables
        ShowBase.__init__(self._showbase)
        self._init_globals()

        # Create the loading screen
        self._loading_screen.create()
        self._adjust_camera_settings()
        self._create_managers()

        # Init the onscreen debugger
        self._init_debugger()

        # Load plugins and daytime settings
        self._plugin_mgr.load_plugins()
        self._daytime_mgr.load_settings()
        self._com_resources.write_config()

        # Setup common defines
        self._create_common_defines()

        # Let the plugins setup their stages
        self._plugin_mgr.trigger_hook("on_stage_setup")
        self._setup_managers()
        self._plugin_mgr.trigger_hook("on_pipeline_created")

        # Set the default effect on render
        self.set_effect(Globals.render, "Effects/Default.yaml", {}, -10)

        # Hide the loading screen
        self._loading_screen.remove()

        self._start_listener()

        # Measure how long it took to initialize everything
        init_duration = int((time.time() - start_time) * 1000.0)
        self.debug("Finished initialization in {} ms".format(init_duration))

    def _create_managers(self):
        """ Internal method to create all managers and instances"""
        self._tag_mgr = TagStateManager(Globals.base.cam)
        self._plugin_mgr = PluginManager(self)
        self._effect_loader = EffectLoader()
        self._stage_mgr = StageManager(self)
        self._light_mgr = LightManager(self)
        self._daytime_mgr = DayTimeManager(self)
        self._ies_profile_mgr = IESProfileManager(self)

        # Load commonly used resources
        self._com_resources = CommonResources(self)
        self._com_stages = CommonStages(self)

    def _setup_managers(self):
        """ Internal method to setup all managers """
        self._stage_mgr.setup()
        self._stage_mgr.set_shaders()
        self._light_mgr.reload_shaders()
        self._init_bindings()
        self._light_mgr.init_shadows()

    def _init_debugger(self):
        """ Internal method to initialize the GUI-based debugger """
        if self.get_setting("pipeline.display_debugger"):
            self._debugger = OnscreenDebugger(self)
        else:
            # Use an empty onscreen debugger in case the debugger is not
            # enabled, which defines all member functions as empty lambdas
            class EmptyDebugger(object):
                def __getattr__(self, *args, **kwargs):
                    return lambda *args, **kwargs: None
            self._debugger = EmptyDebugger()
            del EmptyDebugger

    def _init_globals(self):
        """ Inits all global bindings """
        Globals.load(self._showbase)
        Globals.resolution = LVecBase2i(
            self._showbase.win.get_x_size(),
            self._showbase.win.get_y_size())

        # Connect the render target output function to the debug object
        RenderTarget.RT_OUTPUT_FUNC = lambda *args: DebugObject.global_warn(
            "RenderTarget", *args[1:])

    def _init_bindings(self):
        """ Inits the tasks and keybindings """

        # Add a hotkey to reload the shaders, but only if the debugger is enabled
        if self.get_setting("pipeline.display_debugger"):
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

    def _manager_update_task(self, task):
        """ Update task which gets called before the rendering """
        self._listener.update()
        self._debugger.update()
        self._daytime_mgr.update()
        self._com_resources.update()
        self._stage_mgr.update()
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

        # Work arround buggy nvidia driver, which expects arrays to be const
        if "NVIDIA 361.43" in self._showbase.win.get_gsg().get_driver_version():
            define("CONST_ARRAY", "const")
        else:
            define("CONST_ARRAY", "")

        # Provide driver vendor as a default
        vendor = self._showbase.win.get_gsg().get_driver_vendor().lower()
        if "nvidia" in vendor:
            define("IS_NVIDIA", 1)
        if "ati" in vendor:
            define("IS_AMD", 1)
        if "intel" in vendor:
            define("IS_INTEL", 1)

        self._light_mgr.init_defines()
        self._plugin_mgr.init_defines()

    def _adjust_camera_settings(self):
        """ Sets the default camera settings """
        self._showbase.camLens.set_near_far(0.1, 70000)
        self._showbase.camLens.set_fov(90)

    def _get_mount_mgr(self):
        """ Returns a handle to the mount manager. This can be used for setting
        the base path and also modifying the temp path. See the MountManager
        documentation for further information. """
        return self._mount_mgr

    def _get_stage_mgr(self):
        """ Returns a handle to the stage manager object. The stage manager
        manages all RenderStages, shader inputs and defines, and also writing
        of the shader auto config."""
        return self._stage_mgr

    def _get_plugin_mgr(self):
        """ Returns a handle to the plugin manager, this can be used to trigger
        hooks. It also stores information about the loaded plugins. """
        return self._plugin_mgr

    def _get_light_mgr(self):
        """ Returns a handle to the light manager, this usually should not be used
        by the user, instead use add_light and remove_light. """
        return self._light_mgr

    def _get_tag_mgr(self):
        """ Returns a handle to the tag state manager """
        return self._tag_mgr

    def _get_daytime_mgr(self):
        """ Returns a handle to the DayTime manager """
        return self._daytime_mgr

    # Manager properties
    mount_mgr = property(_get_mount_mgr)
    stage_mgr = property(_get_stage_mgr)
    plugin_mgr = property(_get_plugin_mgr)
    light_mgr = property(_get_light_mgr)
    tag_mgr = property(_get_tag_mgr)
    daytime_mgr = property(_get_daytime_mgr)
