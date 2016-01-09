"""

RenderPipeline

Copyright (c) 2014-2015 tobspr <tobias.springer1@gmail.com>

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
from six import iteritems

from math import ceil

from panda3d.core import NodePath, ShaderAttrib

from ..Globals import Globals
from ..Util.DebugObject import DebugObject
from .PluginConfig import PluginConfig

class BasePlugin(DebugObject):

    """ This is the base plugin class from which all plugins should derive. """

    def __init__(self, pipeline):
        """ Constructs the plugin, also checks if all plugin properties are set
        properly """

        # Find the plugin name:
        # The __module__ contains something like Plugins.XXX.YYY
        # We want XXX so we take the second parameter
        self._id = str(self.__class__.__module__).split(".")[1]
        DebugObject.__init__(self, "Plugin::" + self._id)
        self._pipeline = pipeline
        self._setting_change_handlers = {}
        self._assigned_stages = []
        self._hooks = {}
        self._config = PluginConfig()

        # Set a special output color for plugins
        self._set_debug_color("magenta", "bright")
        self._load_config()

    def init(self):
        """ Inits the plugin """
        self._init_bindings()

    def _init_bindings(self):
        """ Binds all hooks marked with @PluginHook """
        for attr in dir(self):
            val = getattr(self, attr)
            if hasattr(val, "hook_id"):
                self._bind_to_hook(val.hook_id, val)
            if hasattr(val, "setting_id"):
                self._setting_change_handlers[val.setting_id] = val

    def handle_setting_change(self, name):
        """ Gets called when a dynamic setting got called """
        if name in self._setting_change_handlers:
            self._setting_change_handlers[name]()

    def reload_stage_shaders(self):
        """ Reloads all shaders of all stages used by the plugin """
        for stage in self._assigned_stages:
            stage.set_shaders()

    def _load_config(self):
        """ Loads the plugin configuration from the plugin directory """
        expected_path = "Plugins/" + self._id + "/config.yaml"
        self._config.load(expected_path)

    def _bind_to_hook(self, hook_name, handler):
        """ Binds the handler to a given hook_name. When the hook is executed
        in the pipeline code, the handler gets called """
        self._pipeline.plugin_mgr.add_hook_binding(hook_name, handler)
        self._hooks[hook_name] = handler

    def trigger_hook_explicit(self, hook_name):
        """ Triggers a hook for this plugin only. """
        if hook_name in self._hooks:
            self._hooks[hook_name]()

    def define_static_plugin_settings(self):
        """ Makes all plugin settings available in shaders by using defines.
        This ignores settings which are marked as runtime changeable (but includes
        shader runtime settings). """

        for name, setting in iteritems(self._config.get_settings()):
            if not setting.runtime or setting.shader_runtime:
                if setting.type == "ENUM":
                    # define all enum values
                    for idx, value in enumerate(setting.values):
                        self._pipeline.stage_mgr.define(
                            self._id + "_ENUM_" + name + "_" + value, idx)

                    self._pipeline.stage_mgr.define(
                        self._id + "__" + name, setting.values.index(setting.value))

                else:
                    self._pipeline.stage_mgr.define(
                        self._id + "__" + name, setting.value)

    def get_id(self):
        """ Returns the id of the plugin """
        return self._id

    def get_config(self):
        """ Returns a handle to the plugin config object """
        return self._config

    def get_setting(self, name):
        """ Shortcut for get_config().get_setting() """
        return self._config.get_setting(name)

    def get_daytime_setting(self, setting_name, plugin_id=None):
        """ Returns the daytime setting """
        if plugin_id is None:
            plugin_id = self.get_id()
        return self._pipeline.daytime_mgr.get_setting_value(plugin_id, setting_name)

    def get_resource(self, pth):
        """ Converts a local path from the plugins Resource/ directory into
        an absolute path """
        return "Plugins/" + self._id + "/Resources/" + pth.lstrip("/")

    def get_shader_resource(self, pth):
        """ Converts a local path from the plugins Shader/ directory into
        an absolute path """
        return "Plugins/" + self._id + "/Shader/" + pth.lstrip("/")

    def is_plugin_loaded(self, plugin):
        """ Returns whether a plugin is currently loaded """
        return self._pipeline.plugin_mgr.get_interface().has_plugin_handle(plugin)

    def create_stage(self, stage_type):
        """ Shortcut to create a new render stage from a given class type """
        stage_handle = stage_type(self._pipeline)
        self._pipeline.stage_mgr.add_stage(stage_handle)
        self._assigned_stages.append(stage_handle)
        return stage_handle

    def add_define(self, key, value):
        """ Adds a new define. This should be called in the on_stage_setup hook """
        self._pipeline.stage_mgr.define(key, value)

    def exec_compute_shader(self, shader_obj, shader_inputs, exec_size,
                            workgroup_size=(16, 16, 1)):
        """ Executes a compute shader. The shader object should be a shader
        loaded with Shader.load_compute, the shader inputs should be a dict where
        the keys are the names of the shader inputs and the values are the
        inputs. The workgroup_size has to match the size defined in the
        compute shader """
        ntx = int(ceil(exec_size[0] / workgroup_size[0]))
        nty = int(ceil(exec_size[1] / workgroup_size[1]))
        ntz = int(ceil(exec_size[2] / workgroup_size[2]))

        nodepath = NodePath("shader")
        nodepath.set_shader(shader_obj)
        for key, val in iteritems(shader_inputs):
            nodepath.set_shader_input(key, val)

        attr = nodepath.get_attrib(ShaderAttrib)
        Globals.base.graphicsEngine.dispatch_compute(
            (ntx, nty, ntz), attr, Globals.base.win.get_gsg())
