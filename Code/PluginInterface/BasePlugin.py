
from __future__ import division, print_function

from math import ceil

from panda3d.core import NodePath, ShaderAttrib
from direct.stdpy.file import isfile

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
        self._config = PluginConfig()

        # Set a special output color for plugins
        self._set_debug_color("magenta", "bright")
        self._init_bindings()
        self._load_config()

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
        self._pipeline.get_plugin_mgr().add_hook_binding(hook_name, handler)

    def define_static_plugin_settings(self):
        """ Makes all plugin settings available in shaders by using defines.
        This ignores settings which are marked as runtime changeable (but includes
        shader runtime settings). """

        for name, setting in self._config.get_settings().items():
            if not setting.runtime or setting.shader_runtime:
                if setting.type == "ENUM":
                    # define all enum values
                    for idx, value in enumerate(setting.values):
                        self._pipeline.get_stage_mgr().define(self._id + "_ENUM_" + name + "_" + value, idx)

                    self._pipeline.get_stage_mgr().define(self._id + "__" + name, setting.values.index(setting.value))
                
                else:
                    self._pipeline.get_stage_mgr().define(self._id + "__" + name, setting.value)

    def get_id(self):
        """ Returns the id of the plugin """
        return self._id

    def get_config(self):
        """ Returns a handle to the plugin config object """
        return self._config

    def get_setting(self, name):
        """ Shortcut for get_config().get_setting() """
        return self._config.get_setting(name)

    def get_resource(self, pth):
        """ Converts a local path from the plugins Resource/ directory into
        an absolute path """
        return "Plugins/" + self._id + "/Resources/" + pth.lstrip("/")

    def get_shader_resource(self, pth):
        """ Converts a local path from the plugins Shader/ directory into
        an absolute path """
        return "Plugins/" + self._id + "/Shader/" + pth.lstrip("/")

    def create_stage(self, stage_type):
        """ Shortcut to create a new render stage from a given class type """
        stage_handle = stage_type(self._pipeline)
        self._pipeline.get_stage_mgr().add_stage(stage_handle)
        self._assigned_stages.append(stage_handle)
        return stage_handle

    def add_define(self, key, value):
        """ Adds a new define. This should be called in the on_stage_setup hook """
        self._pipeline.get_stage_mgr().define(key, value)

    def exec_compute_shader(self, shader_obj, shader_inputs, exec_size, 
            workgroup_size=(16, 16, 1)):
        """ Executes a compute shader. The shader object should be a shader
        loaded with Shader.load_compute, the shader inputs should be a dict where
        the keys are the names of the shader inputs and the values are the 
        inputs. The workgroup_size has to match the size defined in the 
        compute shader """
        ntx = int(ceil( exec_size[0] / workgroup_size[0]))
        nty = int(ceil( exec_size[1] / workgroup_size[1]))
        ntz = int(ceil( exec_size[2] / workgroup_size[2]))

        np = NodePath("shader")
        np.set_shader(shader_obj)
        for key, val in shader_inputs.items():
            np.set_shader_input(key, val)

        attr = np.get_attrib(ShaderAttrib)
        Globals.base.graphicsEngine.dispatch_compute((ntx, nty, ntz),
            attr, Globals.base.win.get_gsg())
