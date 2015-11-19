
from os.path import join

from ..BasePluginInterface import BasePluginInterface
from .VirtualPlugin import VirtualPlugin
from ..PluginExceptions import BadPluginException, BadSettingException

class VirtualPluginInterface(BasePluginInterface):
    
    """ This is the virtual plugin interface, which extends the given plugin
    interface with methods to load virtual plugins """

    def load_plugins(self):
        """ Loads all plugins as virtual plugins into the pipeline, it can be
        used to access plugin data outside of the pipeline """
        self.load_plugin_config()

        plugin_ids = self.get_available_plugins()

        for plugin in plugin_ids:

            if not self._valid_name_regexp.match(plugin):
                self.warn("Invalid plugin name: '" + plugin + "', skipping ...")
                continue

            # Try loading the plugin, and see what happens
            try:
                plugin_instance = self._load_plugin(plugin)
            except BadPluginException as msg:
                self.warn("Bad plugin", plugin)
                self.warn(msg)
                continue
            except BadSettingException as msg:
                self.warn("Bad setting for", plugin)
                self.warn(msg)
                continue

            # Try applying the overrides, and see what happens
            try:
                plugin_instance.apply_overrides(self._overrides)
            except BadSettingException as msg:
                self.warn("Error applying overrides, bad setting")
                self.warn(msg)
                continue

            self._plugin_instances.append(plugin_instance)

    def get_plugin_handle(self, plugin_id):
        """ Returns a plugin instance by a given id. This is only valid if 
        load_virtual_plugins() was called before, and returns the handle to
        the VirtualPlugin instance. """
        for plugin in self._plugin_instances:
            if plugin.get_id() == plugin_id:
                return plugin
        return None

    def _load_plugin(self, plugin_id):
        """ Internal method to load a plugin into memory """
        instance = VirtualPlugin(plugin_id)
        instance.set_plugin_path(join(self._base_dir, "Plugins", plugin_id))
        instance.load()
        return instance

    def get_plugin_instances(self):
        """ Returns a list of all virtual plugin instances, this is only valid
        after load_virtual_plugins() was called. """
        return self._plugin_instances

    def unload_plugins(self):
        """ Unloads all virtual plugin instances """
        self._plugin_instances = []

    def update_setting(self, plugin_id, setting_id, new_value):
        """ Updates a virtual plugin setting """
        plugin = self.get_plugin_handle(plugin_id)
        setting = plugin.get_config().get_setting_handle(setting_id)
        setting.set_value(new_value)
        override_key = plugin_id + "." + setting_id
        self._overrides[override_key] = setting.value
