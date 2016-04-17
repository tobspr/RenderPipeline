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
import math

from panda3d.core import LVecBase2i, TransformState, RenderState, load_prc_file
from panda3d.core import PandaSystem, MaterialAttrib
from direct.showbase.ShowBase import ShowBase
from direct.stdpy.file import isfile

from rplibs.yaml import load_yaml_file_flat
from rplibs.six.moves import range

from rpcore.globals import Globals
from rpcore.effect import Effect
from rpcore.common_resources import CommonResources
from rpcore.native import TagStateManager, PointLight, SpotLight
from rpcore.render_target import RenderTarget
from rpcore.pluginbase.manager import PluginManager
from rpcore.pluginbase.day_manager import DayTimeManager
from rpcore.util.task_scheduler import TaskScheduler

from rpcore.rpobject import RPObject
from rpcore.util.network_communication import NetworkCommunication
from rpcore.util.ies_profile_loader import IESProfileLoader

from rpcore.gui.debugger import Debugger
from rpcore.gui.loading_screen import LoadingScreen, EmptyLoadingScreen

from rpcore.mount_manager import MountManager
from rpcore.stage_manager import StageManager
from rpcore.light_manager import LightManager

from rpcore.stages.ambient_stage import AmbientStage
from rpcore.stages.gbuffer_stage import GBufferStage
from rpcore.stages.final_stage import FinalStage
from rpcore.stages.downscale_z_stage import DownscaleZStage
from rpcore.stages.combine_velocity_stage import CombineVelocityStage
from rpcore.stages.upscale_stage import UpscaleStage


class RenderPipeline(RPObject):

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
        self.debug("Using Python {}.{} with architecture {}".format(
            sys.version_info.major, sys.version_info.minor, PandaSystem.get_platform()))
        self.debug("Using Panda3D {} built on {}".format(
            PandaSystem.get_version_string(), PandaSystem.get_build_date()))
        if PandaSystem.get_git_commit():
            self.debug("Using git commit {}".format(PandaSystem.get_git_commit()))
        else:
            self.debug("Using custom Panda3D build")
        self.mount_mgr = MountManager(self)
        self.settings = {}
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
        self.settings = load_yaml_file_flat(path)

    def reload_shaders(self):
        """ Reloads all shaders """
        if self.settings["pipeline.display_debugger"]:
            self.debug("Reloading shaders ..")
            self._debugger.get_error_msg_handler().clear_messages()
            self._debugger.set_reload_hint_visible(True)
            self._showbase.graphicsEngine.render_frame()
            self._showbase.graphicsEngine.render_frame()

        self.tag_mgr.cleanup_states()
        self.stage_mgr.reload_shaders()
        self.light_mgr.reload_shaders()

        # Set the default effect on render and trigger the reload hook
        self._set_default_effect()
        self.plugin_mgr.trigger_hook("shader_reload")

        if self.settings["pipeline.display_debugger"]:
            self._debugger.set_reload_hint_visible(False)

    def pre_showbase_init(self):
        """ Setups all required pipeline settings and configuration which have
        to be set before the showbase is setup. This is called by create(),
        in case the showbase was not initialized, however you can (and have to)
        call it manually before you init your custom showbase instance.
        See the 00-Loading the pipeline sample for more information."""

        if not self.mount_mgr.is_mounted:
            self.debug("Mount manager was not mounted, mounting now ...")
            self.mount_mgr.mount()

        if not self.settings:
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
        self.plugin_mgr.load()
        self.daytime_mgr.load_settings()
        self._com_resources.write_config()

        # Init the onscreen debugger
        self._init_debugger()

        # Let the plugins setup their stages
        self.plugin_mgr.trigger_hook("stage_setup")

        self._create_common_defines()
        self._setup_managers()
        self._create_default_skybox()

        self.plugin_mgr.trigger_hook("pipeline_created")

        # Hide the loading screen
        self._loading_screen.remove()

        # Start listening for updates
        self._listener = NetworkCommunication(self)
        self._set_default_effect()

        # Measure how long it took to initialize everything
        init_duration = (time.time() - start_time)
        self.debug("Finished initialization in {:3.3f} s".format(init_duration))

        self._first_frame = time.clock()

    def _create_managers(self):
        """ Internal method to create all managers and instances"""
        self.task_scheduler = TaskScheduler(self)
        self.tag_mgr = TagStateManager(Globals.base.cam)
        self.plugin_mgr = PluginManager(self)
        self.stage_mgr = StageManager(self)
        self.light_mgr = LightManager(self)
        self.daytime_mgr = DayTimeManager(self)
        self.ies_loader = IESProfileLoader(self)

        # Load commonly used resources
        self._com_resources = CommonResources(self)
        self._init_common_stages()

    def _setup_managers(self):
        """ Internal method to setup all managers """
        self.stage_mgr.setup()
        self.stage_mgr.reload_shaders()
        self.light_mgr.reload_shaders()
        self._init_bindings()
        self.light_mgr.init_shadows()

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

        scale_factor = self.settings["pipeline.resolution_scale"]
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
        self._showbase.addTask(self._update_inputs_and_stages, "RP_UpdateInputsAndStages", sort=18)
        self._showbase.taskMgr.doMethodLater(0.5, self._clear_state_cache, "RP_ClearStateCache")

    def _clear_state_cache(self, task=None):
        """ Task which repeatedly clears the state cache to avoid storing
        unused states. """
        task.delayTime = 2.0
        TransformState.clear_cache()
        RenderState.clear_cache()
        return task.again

    def _manager_update_task(self, task):
        """ Update task which gets called before the rendering """
        self.task_scheduler.step()
        self._listener.update()
        self._debugger.update()
        self.daytime_mgr.update()
        self.light_mgr.update()
        return task.cont

    def _update_inputs_and_stages(self, task):
        """ Updates teh commonly used inputs """
        self._com_resources.update()
        self.stage_mgr.update()
        return task.cont

    def _plugin_pre_render_update(self, task):
        """ Update task which gets called before the rendering, and updates the
        plugins. This is a seperate task to split the work, and be able to do
        better performance analysis """
        self.plugin_mgr.trigger_hook("pre_render_update")
        return task.cont

    def _plugin_post_render_update(self, task):
        """ Update task which gets called after the rendering """
        self.plugin_mgr.trigger_hook("post_render_update")

        if self._first_frame is not None:
            duration = time.clock() - self._first_frame
            self.debug("Took", round(duration, 3), "s until first frame")
            self._first_frame = None

        return task.cont

    def _create_common_defines(self):
        """ Creates commonly used defines for the shader auto config """
        defines = self.stage_mgr.defines

        # 3D viewport size
        defines["WINDOW_WIDTH"] = Globals.resolution.x
        defines["WINDOW_HEIGHT"] = Globals.resolution.y

        # Actual window size - might differ for supersampling
        defines["NATIVE_WINDOW_WIDTH"] = Globals.base.win.get_x_size()
        defines["NATIVE_WINDOW_HEIGHT"] = Globals.base.win.get_y_size()

        # Pass camera near and far plane
        defines["CAMERA_NEAR"] = round(Globals.base.camLens.get_near(), 10)
        defines["CAMERA_FAR"] = round(Globals.base.camLens.get_far(), 10)

        # Work arround buggy nvidia driver, which expects arrays to be const
        if "NVIDIA 361.43" in self._showbase.win.get_gsg().get_driver_version():
            defines["CONST_ARRAY"] = "const"
        else:
            defines["CONST_ARRAY"] = ""

        # Provide driver vendor as a default
        vendor = self._showbase.win.get_gsg().get_driver_vendor().lower()
        if "nvidia" in vendor:
            defines["IS_NVIDIA"] = 1
        if "ati" in vendor:
            defines["IS_AMD"] = 1
        if "intel" in vendor:
            defines["IS_INTEL"] = 1

        defines["REFERENCE_MODE"] = self.settings["pipeline.reference_mode"]

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
            defines["EXPERIMENTAL_PREV_TRANSFORM"] = 1

        self.light_mgr.init_defines()
        self.plugin_mgr.init_defines()

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
        self._loading_screen = LoadingScreen(self)

    def set_empty_loading_screen(self):
        """ Tells the pipeline to use no loading screen """
        self._loading_screen = EmptyLoadingScreen()

    @property
    def loading_screen(self):
        """ Returns the current loading screen """
        return self._loading_screen

    def add_light(self, light):
        """ Adds a new light to the rendered lights, check out the LightManager
        add_light documentation for further information. """
        self.light_mgr.add_light(light)

    def remove_light(self, light):
        """ Removes a previously attached light, check out the LightManager
        remove_light documentation for further information. """
        self.light_mgr.remove_light(light)

    def _create_default_skybox(self, size=40000):
        """ Returns the default skybox, with a scale of <size>, and all
        proper effects and shaders already applied. The skybox is already
        parented to render as well. """
        skybox = self._com_resources.load_default_skybox()
        skybox.set_scale(size)
        skybox.reparent_to(Globals.render)
        skybox.set_bin("unsorted", 10000)
        self.set_effect(skybox, "effects/skybox.yaml", {
            "render_shadows":   False,
            "render_envmap":    False,
            "render_voxel":     False,
            "alpha_testing":    False,
            "normal_mapping":   False,
            "parallax_mapping": False
        }, 1000)
        return skybox

    def load_ies_profile(self, filename):
        """ Loads an IES profile from a given filename and returns a handle which
        can be used to set an ies profile on a light """
        return self.ies_loader.load(filename)

    def set_effect(self, nodepath, effect_src, options=None, sort=30):
        """ Sets an effect to the given object, using the specified options.
        Check out the effect documentation for more information about possible
        options and configurations. The object should be a nodepath, and the
        effect will be applied to that nodepath and all nodepaths below whose
        current effect sort is less than the new effect sort (passed by the
        sort parameter). """

        effect = Effect.load(effect_src, options)
        if effect is None:
            return self.error("Could not apply effect")

        # Apply default stage shader
        if not effect.get_option("render_gbuffer"):
            nodepath.hide(self.tag_mgr.gbuffer_mask)
        else:
            nodepath.set_shader(effect.get_shader_obj("gbuffer"), sort)
            nodepath.show(self.tag_mgr.gbuffer_mask)

        # Apply shadow stage shader
        if not effect.get_option("render_shadows"):
            nodepath.hide(self.tag_mgr.shadow_mask)
        else:
            shader = effect.get_shader_obj("shadows")
            self.tag_mgr.apply_state(
                "shadow", nodepath, shader, str(effect.effect_id), 25 + sort)
            nodepath.show(self.tag_mgr.shadow_mask)

        # Apply voxelization stage shader
        if not effect.get_option("render_voxel"):
            nodepath.hide(self.tag_mgr.voxelize_mask)
        else:
            shader = effect.get_shader_obj("voxelize")
            self.tag_mgr.apply_state(
                "voxelize", nodepath, shader, str(effect.effect_id), 35 + sort)
            nodepath.show(self.tag_mgr.voxelize_mask)

        # Apply envmap stage shader
        if not effect.get_option("render_envmap"):
            nodepath.hide(self.tag_mgr.envmap_mask)
        else:
            shader = effect.get_shader_obj("envmap")
            self.tag_mgr.apply_state(
                "envmap", nodepath, shader, str(effect.effect_id), 45 + sort)
            nodepath.show(self.tag_mgr.envmap_mask)

        # Apply forward shading shader
        if not effect.get_option("render_forward"):
            nodepath.hide(self.tag_mgr.forward_mask)
        else:
            shader = effect.get_shader_obj("forward")
            self.tag_mgr.apply_state(
                "forward", nodepath, shader, str(effect.effect_id), 55 + sort)
            nodepath.show_through(self.tag_mgr.forward_mask)

        # Check for invalid options
        if effect.get_option("render_gbuffer") and effect.get_option("render_forward"):
            self.error("You cannot render an object forward and deferred at the same time! Either "
                       "use render_gbuffer or use render_forward, but not both.")

    def add_environment_probe(self):
        """ Constructs a new environment probe and returns the handle, so that
        the probe can be modified """

        # TODO: This method is super hacky
        if not self.plugin_mgr.is_plugin_enabled("env_probes"):
            self.warn("EnvProbe plugin is not loaded, can not add environment probe")
            class DummyEnvironmentProbe(object):
                def __getattr__(self, *args, **kwargs):
                    return lambda *args, **kwargs: None
            return DummyEnvironmentProbe()

        from rpplugins.env_probes.environment_probe import EnvironmentProbe
        probe = EnvironmentProbe()
        self.plugin_mgr.instances["env_probes"].probe_mgr.add_probe(probe)
        return probe

    def prepare_scene(self, scene):
        """ Prepares a given scene, by converting panda lights to render pipeline
        lights """

        # TODO: IES profiles
        ies_profile = self.load_ies_profile("soft_display.ies") # pylint: disable=W0612
        lights = []

        for light in scene.find_all_matches("**/+PointLight"):
            light_node = light.node()
            rp_light = PointLight()
            rp_light.pos = light.get_pos(Globals.base.render)
            rp_light.radius = light_node.max_distance
            rp_light.energy = 100.0 * light_node.color.w
            rp_light.color = light_node.color.xyz
            rp_light.casts_shadows = light_node.shadow_caster
            rp_light.shadow_map_resolution = light_node.shadow_buffer_size.x
            rp_light.inner_radius = 0.8
            self.add_light(rp_light)
            light.remove_node()
            lights.append(rp_light)

        for light in scene.find_all_matches("**/+Spotlight"):
            light_node = light.node()
            rp_light = SpotLight()
            rp_light.pos = light.get_pos(Globals.base.render)
            rp_light.radius = light_node.max_distance
            rp_light.energy = 100.0 * light_node.color.w
            rp_light.color = light_node.color.xyz
            rp_light.casts_shadows = light_node.shadow_caster
            rp_light.shadow_map_resolution = light_node.shadow_buffer_size.x
            rp_light.fov = light_node.exponent / math.pi * 180.0
            lpoint = light.get_mat(Globals.base.render).xform_vec((0, 0, -1))
            rp_light.direction = lpoint
            self.add_light(rp_light)
            light.remove_node()
            lights.append(rp_light)

        envprobes = []

        # Add environment probes
        for np in scene.find_all_matches("**/ENVPROBE*"):
            probe = self.add_environment_probe()
            probe.set_mat(np.get_mat())
            probe.border_smoothness = 0.001
            probe.parallax_correction = True
            np.remove_node()
            envprobes.append(probe)

        # Find transparent objects and set the right effect
        for geom_np in scene.find_all_matches("**/+GeomNode"):
            geom_node = geom_np.node()
            geom_count = geom_node.get_num_geoms()
            for i in range(geom_count):
                state = geom_node.get_geom_state(i)
                if not state.has_attrib(MaterialAttrib):
                    self.warn("Geom", geom_node, "has no material!")
                    continue
                material = state.get_attrib(MaterialAttrib).get_material()
                shading_model = material.emission.x

                # SHADING_MODEL_TRANSPARENT
                if shading_model == 3:
                    if geom_count > 1:
                        self.error("Transparent materials must have their own geom!")
                        continue

                    self.set_effect(
                        geom_np, "effects/default.yaml",
                        {"render_forward": True, "render_gbuffer": False}, 100)

                 # SHADING_MODEL_FOLIAGE
                elif shading_model == 5:
                    # XXX: Maybe only enable alpha testing for foliage unless
                    # specified otherwise
                    pass


        return {"lights": lights, "envprobes": envprobes}

    def _check_version(self):
        """ Internal method to check if the required Panda3D version is met. Returns
        True if the version is new enough, and False if the version is outdated. """

        from panda3d.core import PointLight as Panda3DPointLight
        if not hasattr(Panda3DPointLight(""), "shadow_caster"):
            return False

        return True

    def _init_common_stages(self):
        """ Inits the commonly used stages, which don't belong to any plugin,
        but yet are necessary and widely used. """
        add_stage = self.stage_mgr.add_stage

        self._ambient_stage = AmbientStage(self)
        add_stage(self._ambient_stage)

        self._gbuffer_stage = GBufferStage(self)
        add_stage(self._gbuffer_stage)

        self._final_stage = FinalStage(self)
        add_stage(self._final_stage)

        self._downscale_stage = DownscaleZStage(self)
        add_stage(self._downscale_stage)

        self._combine_velocity_stage = CombineVelocityStage(self)
        add_stage(self._combine_velocity_stage)

        # Add an upscale/downscale stage in case we render at a different resolution
        if abs(1 - self.settings["pipeline.resolution_scale"]) > 0.05:
            self._upscale_stage = UpscaleStage(self)
            add_stage(self._upscale_stage)

    def _set_default_effect(self):
        """ Sets the default effect used for all objects if not overridden """
        self.set_effect(Globals.render, "effects/default.yaml", {}, -10)

    def _adjust_camera_settings(self):
        """ Sets the default camera settings """
        self._showbase.camLens.set_near_far(0.1, 70000)
        self._showbase.camLens.set_fov(60)
