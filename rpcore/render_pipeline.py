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

from __future__ import division, print_function

import sys
import time

from panda3d.core import LVecBase2i, TransformState, RenderState, load_prc_file
from panda3d.core import PandaSystem
from direct.showbase.ShowBase import ShowBase
from direct.stdpy.file import isfile

from rplibs.yaml import load_yaml_file_flat

from rpcore.globals import Globals
from rpcore.pipeline_extensions import PipelineExtensions
from rpcore.common_resources import CommonResources
from rpcore.native import TagStateManager
from rpcore.render_target import RenderTarget
from rpcore.pluginbase.manager import PluginManager
from rpcore.pluginbase.day_manager import DayTimeManager

from rpcore.rpobject import RPObject
from rpcore.util.network_update_listener import NetworkUpdateListener
from rpcore.util.ies_profile_loader import IESProfileLoader
from rpcore.gui.debugger import Debugger

from rpcore.mount_manager import MountManager
from rpcore.stage_manager import StageManager
from rpcore.light_manager import LightManager


class RenderPipeline(PipelineExtensions, RPObject):

    """ This is the main pipeline logic, it combines all components of the
    pipeline to form a working system. It does not do much work itself, but
    instead setups all the managers and systems to be able to do their work.

    It also derives from RPExtensions to provide some useful functions like
    creating a default skybox or loading effect files. """

    def __init__(self, outdated_parameter=None):
        """ Creates a new pipeline with a given showbase instance. This should
        be done before intializing the ShowBase, the pipeline will take care of
        that. """
        RPObject.__init__(self)
        if outdated_parameter is not None:
            self.fatal("The render pipeline no longer takes the ShowBase argument "
                       "as constructor parameter. Please have a look at the "
                       "00-Loading the pipeline sample to see how to initialize "
                       "the pipeline properly.")
        self.debug("Using Python {} with architecture {}".format(
            sys.version_info.major, PandaSystem.get_platform()))
        self.debug("Using Panda3D {} built on {}".format(
            PandaSystem.get_version_string(), PandaSystem.get_build_date()))
        if PandaSystem.get_git_commit():
            self.debug("Using git commit {}".format(PandaSystem.get_git_commit()))
        else:
            self.debug("Using custom Panda3D build")
        self._mount_mgr = MountManager(self)
        self._settings = {}
        self._pre_showbase_initialized = False
        self._first_frame = None
        self.set_default_loading_screen()

        # Check for the right Panda3D version
        if not self._check_version():
            self.fatal("Your Panda3D version is outdated! Please update to the newest \n"
                       "git version! Checkout https://github.com/panda3d/panda3d to "
                       "compile panda from source, or get a recent buildbot build.")

    def load_settings(self, path):
        """ Loads the pipeline configuration from a given filename. Usually
        this is the 'config/pipeline.ini' file. If you call this more than once,
        only the settings of the last file will be used. """
        self._settings = load_yaml_file_flat(path)

    @property
    def settings(self):
        """ Returns a handle to the settings instance, which can be used to
        query settings """
        return self._settings

    @property
    def mount_mgr(self):
        """ Returns a handle to the mount manager. This can be used for setting
        the base path and also modifying the temp path. See the MountManager
        documentation for further information. """
        return self._mount_mgr

    @property
    def stage_mgr(self):
        """ Returns a handle to the stage manager object. The stage manager
        manages all RenderStages, shader inputs and defines, and also writing
        of the shader auto config."""
        return self._stage_mgr

    @property
    def plugin_mgr(self):
        """ Returns a handle to the plugin manager, this can be used to trigger
        hooks. It also stores information about the loaded plugins. """
        return self._plugin_mgr

    @property
    def light_mgr(self):
        """ Returns a handle to the light manager, this usually should not be used
        by the user, instead use add_light and remove_light. """
        return self._light_mgr

    @property
    def tag_mgr(self):
        """ Returns a handle to the tag-state manager, which can be used to register
        new cameras """
        return self._tag_mgr

    @property
    def daytime_mgr(self):
        """ Returns a handle to the DayTime manager, which can be used to control
        the time of day """
        return self._daytime_mgr

    def reload_shaders(self):
        """ Reloads all shaders """
        if self.settings["pipeline.display_debugger"]:
            self.debug("Reloading shaders ..")
            self._debugger.get_error_msg_handler().clear_messages()
            self._debugger.set_reload_hint_visible(True)
            self._showbase.graphicsEngine.render_frame()
            self._showbase.graphicsEngine.render_frame()

        self._tag_mgr.cleanup_states()
        self._stage_mgr.reload_shaders()
        self._light_mgr.reload_shaders()

        # Set the default effect on render and trigger the reload hook
        self._set_default_effect()
        self._plugin_mgr.trigger_hook("shader_reload")

        if self.settings["pipeline.display_debugger"]:
            self._debugger.set_reload_hint_visible(False)

    def pre_showbase_init(self):
        """ Setups all required pipeline settings and configuration which have
        to be set before the showbase is setup. This is called by create(),
        in case the showbase was not initialized, however you can (and have to)
        call it manually before you init your custom showbase instance.
        See the 00-Loading the pipeline sample for more information."""

        if not self._mount_mgr.is_mounted:
            self.debug("Mount manager was not mounted, mounting now ...")
            self._mount_mgr.mount()

        if not self._settings:
            self.debug("No settings loaded, loading from default location")
            self.load_settings("/$$rpconfig/pipeline.yaml")

        # Check if the pipeline was properly installed, before including anything else
        if not isfile("/$$rp/data/install.flag"):
            self.fatal("You didn't setup the pipeline yet! Please run setup.py.")

        # Load the default prc config
        load_prc_file("/$$rpconfig/panda3d-config.prc")

        # Set the initialization flag
        self._pre_showbase_initialized = True

    def create(self, base=None):
        """ This creates the pipeline, and setups all buffers. It also
        constructs the showbase. The settings should have been loaded before
        calling this, and also the base and write path should have been
        initialized properly (see MountManager).

        If base is None, the showbase used in the RenderPipeline constructor
        will be used and initialized. Otherwise it is assumed that base is an
        initialized ShowBase object. In this case, you should call
        pre_showbase_init() before initializing the ShowBase"""

        start_time = time.time()
        self._init_showbase(base)
        self._init_globals()

        # Create the loading screen
        self._loading_screen.create()
        self._adjust_camera_settings()
        self._create_managers()

        # Load plugins and daytime settings
        self._plugin_mgr.load()
        self._daytime_mgr.load_settings()
        self._com_resources.write_config()

        # Init the onscreen debugger
        self._init_debugger()

        # Let the plugins setup their stages
        self._plugin_mgr.trigger_hook("stage_setup")

        self._create_common_defines()
        self._setup_managers()
        self._create_default_skybox()

        self._plugin_mgr.trigger_hook("pipeline_created")

        # Hide the loading screen
        self._loading_screen.remove()
        self._start_listener()
        self._set_default_effect()

        # Measure how long it took to initialize everything
        init_duration = (time.time() - start_time)
        self.debug("Finished initialization in {:3.3f} s".format(init_duration))

        self._first_frame = time.clock()

    def _create_managers(self):
        """ Internal method to create all managers and instances"""
        self._tag_mgr = TagStateManager(Globals.base.cam)
        self._plugin_mgr = PluginManager(self)
        self._stage_mgr = StageManager(self)
        self._light_mgr = LightManager(self)
        self._daytime_mgr = DayTimeManager(self)
        self._ies_loader = IESProfileLoader(self)

        # Load commonly used resources
        self._com_resources = CommonResources(self)
        self._init_common_stages()

    def _setup_managers(self):
        """ Internal method to setup all managers """
        self._stage_mgr.setup()
        self._stage_mgr.reload_shaders()
        self._light_mgr.reload_shaders()
        self._init_bindings()
        self._light_mgr.init_shadows()

    def _init_debugger(self):
        """ Internal method to initialize the GUI-based debugger """
        if self.settings["pipeline.display_debugger"]:
            self._debugger = Debugger(self)
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
        w, h = self._showbase.win.get_x_size(), self._showbase.win.get_y_size()

        scale_factor = self._settings["pipeline.resolution_scale"]
        w = int(float(w) * scale_factor)
        h = int(float(h) * scale_factor)

        # Make sure the resolution is a multiple of 4
        w = w - w % 4
        h = h - h % 4

        self.debug("Render resolution is", w, "x", h)
        Globals.resolution = LVecBase2i(w, h)

        # Connect the render target output function to the debug object
        RenderTarget.RT_OUTPUT_FUNC = lambda *args: RPObject.global_warn(
            "RenderTarget", *args[1:])

        RenderTarget.USE_R11G11B10 = self.settings["pipeline.use_r11_g11_b10"]

    def _init_showbase(self, base):
        """ Inits the the given showbase object """

        # Construct the showbase and init global variables
        if base:
            # Check if we have to init the showbase
            if not hasattr(base, "render"):
                self.pre_showbase_init()
                ShowBase.__init__(base)
            else:
                if not self._pre_showbase_initialized:
                    self.fatal("You constructed your own ShowBase object but you "
                               "did not call pre_show_base_init() on the render "
                               "pipeline object before! Checkout the 00-Loading the "
                               "pipeline sample to see how to initialize the RP.")
            self._showbase = base
        else:
            self.pre_showbase_init()
            self._showbase = ShowBase()

    def _init_bindings(self):
        """ Inits the tasks and keybindings """

        # Add a hotkey to reload the shaders, but only if the debugger is enabled
        if self.settings["pipeline.display_debugger"]:
            self._showbase.accept("r", self.reload_shaders)

        self._showbase.addTask(self._manager_update_task, "RP_UpdateManagers", sort=10)
        self._showbase.addTask(self._plugin_pre_render_update, "RP_Plugin_BeforeRender", sort=12)
        self._showbase.addTask(self._plugin_post_render_update, "RP_Plugin_AfterRender", sort=15)
        self._showbase.addTask(self._update_common_inputs, "RP_UpdateCommonInputs", sort=20)
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
        self._stage_mgr.update()
        self._light_mgr.update()
        # import time
        # time.sleep(0.1)
        return task.cont

    def _update_common_inputs(self, task):
        """ Updates teh commonly used inputs """
        self._com_resources.update()
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

        if self._first_frame is not None:
            duration = time.clock() - self._first_frame
            self.debug("Took", round(duration, 3), "s until first frame")
            self._first_frame = None

        return task.cont

    def _create_common_defines(self):
        """ Creates commonly used defines for the shader auto config """
        define = self._stage_mgr.define

        # 3D viewport size
        define("WINDOW_WIDTH", Globals.resolution.x)
        define("WINDOW_HEIGHT", Globals.resolution.y)

        # Actual window size - might differ for supersampling
        define("NATIVE_WINDOW_WIDTH", Globals.base.win.get_x_size())
        define("NATIVE_WINDOW_HEIGHT", Globals.base.win.get_y_size())

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

        define("REFERENCE_MODE", self.settings["pipeline.reference_mode"])

        # Only activate this experimental feature if the patch was applied,
        # since it is a local change in my Panda3D build which is not yet
        # reviewed by rdb. Once it is in public Panda3D Dev-Builds this will
        # be the default.
        if (not isfile("/$$rp/data/panda3d_patches/prev-model-view-matrix.diff") or
                isfile("D:/__dev__")):

            # You can find the required patch in
            # data/panda3d_patches/prev-model-view-matrix.diff.
            # Delete it after you applied it, so the render pipeline knows the
            # patch is available.
            self.warn("Experimental feature activated, no guarantee it works!")
            define("EXPERIMENTAL_PREV_TRANSFORM", 1)

        self._light_mgr.init_defines()
        self._plugin_mgr.init_defines()
