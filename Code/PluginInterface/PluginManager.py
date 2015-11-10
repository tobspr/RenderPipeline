
import re
import importlib

from direct.stdpy.file import open, isfile

from ..Util.DebugObject import DebugObject

from ..External.PyYAML import YAMLEasyLoad

class PluginManager(DebugObject):

    """ This class manages the loading and handling of plugins """

    def __init__(self, pipeline):
        DebugObject.__init__(self)
        self._pipeline = pipeline
        self._valid_name_regexp = re.compile('^[a-zA-Z0-9_]+$')
        self._plugin_instances = []
        self._enabled_plugins = self._load_plugin_config()
        self._hooks = {}

    def load_plugins(self):
        """ Loads all plugins from the plugin directory """
        self.debug("Loading plugins ..")
        failed_plugins = []
        for plugin in self._enabled_plugins:
            plugin_class = self._try_load_plugin(plugin)
            if plugin_class:
                plugin_instance = plugin_class(self._pipeline)
                self._plugin_instances.append(plugin_instance)
                self.debug("Loaded", plugin_instance.get_config().get_name(), "version",
                    plugin_instance.get_config().get_version())
            else:
                failed_plugins.append(plugin)

        # Unregister plugins which failed to load
        for plugin in failed_plugins:
            self._enabled_plugins.remove(plugin)


    def _load_plugin_config(self):
        """ Loads the plugin config and extracts the list of activated plugins """
        plugin_cfg = "Config/plugins.yaml"

        # Get file content and parse it
        parsed_yaml = YAMLEasyLoad(plugin_cfg)

        # Find root key
        if "enabled" not in parsed_yaml:
            self.warn("Malformed plugin config, could not find root entry!")
            self.warn("Disabling all plugins ...")
            return []

        # In case no plugins are activated, the root key is just None, return
        # an empty list in that case
        if parsed_yaml["enabled"] is None:
            return set()

        # Make the plugin a list a set, to make sure we don't have entries twice
        return set(parsed_yaml["enabled"])

    def _try_load_plugin(self, plugin_id):
        """ Attempts to load a plugin with a given name """
        plugin_path = "Plugins/" + plugin_id + "/"
        plugin_main = plugin_path + "__init__.py"
        if not isfile(plugin_main):
            self.warn("Cannot load",plugin_id,"because __init__.py was not found")
            return None

        module_path = "Plugins." + plugin_id + ".Plugin"

        try:
            module = importlib.import_module(module_path)
        except Exception as msg:
            self.warn("Could not import",plugin_id,"because of an import error:")
            self.warn(msg)
            return None
            
        if not hasattr(module, "Plugin"):
            self.warn("Plugin",plugin_id,"has no main Plugin class defined!")
            return None

        return module.Plugin

    def add_hook_binding(self, hook_name, handler):
        """ Attaches a new handler to a hook """
        if hook_name in self._hooks:
            self._hooks[hook_name].append(handler)
        else:
            self._hooks[hook_name] = [handler]

    def trigger_hook(self, hook_name):
        """ Triggers a hook, executing all handlers attached to that hook """
        if hook_name in self._hooks:
            for handler in self._hooks[hook_name]:
                handler()
                
    def init_defines(self):
        """ Creates the defines which can be used in shaders """
        self.debug("Initializing defines")
        for plugin in self._enabled_plugins:
            self._pipeline.get_stage_mgr().define("HAVE_PLUGIN_" + plugin, 1)



