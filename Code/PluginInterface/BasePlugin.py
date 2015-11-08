
from __future__ import division

from math import ceil

from ..Globals import Globals
from ..Util.DebugObject import DebugObject
from panda3d.core import NodePath, ShaderAttrib

class BasePlugin(DebugObject):

    """ This is the base plugin class from which all plugins should derive. """

    def __init__(self, pipeline):
        """ Constructs the plugin, also checks if all plugin properties are set
        properly """
        DebugObject.__init__(self, "Plugin::" + self.NAME)
        self._pipeline = pipeline

        # Set a special output color for plugins
        self._set_debug_color("magenta", "bright")
        
        for attr in dir(self):
            val = getattr(self, attr)
            if hasattr(val, "hook_id"):
                self._bind_to_hook(val.hook_id, val)

    def __getitem__(self, name):
        """ Handy function to access the settings of the plugin """
        return self.SETTINGS[name].value()

    def _bind_to_hook(self, hook_name, handler):
        """ Binds the handler to a given hook_name. When the hook is executed
        in the pipeline code, the handler gets called """
        self._pipeline.get_plugin_mgr().add_hook_binding(hook_name, handler)

    def get_resource(self, pth):
        """ Converts a local path from the plugins Resource/ directory into
        an absolute path """
        return "Plugins/" + self.NAME + "/Resources/" + pth.lstrip("/")

    def get_shader_resource(self, pth):
        """ Converts a local path from the plugins Shader/ directory into
        an absolute path """
        return "Plugins/" + self.NAME + "/Shader/" + pth.lstrip("/")

    def register_stage(self, stage):
        """ Shortcut to register a render stage """
        self._pipeline.get_stage_mgr().add_stage(stage)

    def make_stage(self, stage_type):
        """ Shortcut to create a new render stage from a given class type """
        return stage_type(self._pipeline)

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
