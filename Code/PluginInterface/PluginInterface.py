

import importlib

from direct.stdpy.file import isfile, join

from .BasePluginInterface import BasePluginInterface
from ..Native import NATIVE_CXX_LOADED

class PluginInterface(BasePluginInterface):

    """ Implementation of the plugin interface which is used by the pipeline """

    def __init__(self, pipeline):
        BasePluginInterface.__init__(self)
        self._pipeline = pipeline
        self._plugin_instances = []

    def load_plugins(self):
        """ Loads all plugins from the plugin directory """
        self.debug("Loading plugins ..")
        failed_plugins = []

        # Try to load all enabled plugins
        for plugin in self.get_enabled_plugins():
            plugin_class = self._try_load_plugin(plugin)

            if plugin_class:
                # In case the plugin loaded, create a instance of it, register
                # the settings and initializes it.
                plugin_instance = plugin_class(self._pipeline)

                # Check if the plugin instance requires the native modules
                if not NATIVE_CXX_LOADED and plugin_instance.get_config().get_requires_native():
                    self.error("Disabling plugin " + plugin_instance.get_id() + ", since it "
                               "requires the C++ modules which are not enabled!")
                    del plugin_instance
                    continue

                plugin_instance.init()
                plugin_instance.get_config().apply_overrides(
                    plugin, self.get_overrides())
                self._plugin_instances.append(plugin_instance)
                self.debug("Loaded", plugin_instance.get_config().get_name())
            else:
                failed_plugins.append(plugin)

        # Unregister plugins which failed to load
        for plugin in failed_plugins:
            self.disable_plugin(plugin)

    def reload_overrides(self):
        """ Reloads the overrides """
        for plugin in self._plugin_instances:
            plugin.get_config().apply_overrides(
                plugin.get_id(), self.get_overrides())

    def get_plugin_handle(self, plugin_id):
        """ Returns a handle to the plugin given its id, or None if the plugin
        could not be found """
        for instance in self._plugin_instances:
            if instance.get_id() == plugin_id:
                return instance
        return None

    def get_plugin_instances(self):
        """ Returns a list of plugin instances """
        return self._plugin_instances

    def _try_load_plugin(self, plugin_id):
        """ Attempts to load a plugin with a given name """
        plugin_path = join(self._base_dir, "Plugins", plugin_id)
        plugin_main = join(plugin_path, "__init__.py")
        if not isfile(plugin_main):
            self.warn("Cannot load", plugin_id, "because __init__.py was not found")
            return None

        module_path = "Plugins." + plugin_id + ".Plugin"

        try:
            module = importlib.import_module(module_path)
        except Exception as msg:
            self.warn("Could not import", plugin_id, "because of an import error:")
            self.warn(msg)
            return None

        if not hasattr(module, "Plugin"):
            self.warn("Plugin", plugin_id, "has no main Plugin class defined!")
            return None

        return module.Plugin
