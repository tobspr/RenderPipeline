from __future__ import print_function 

from direct.stdpy.file import listdir, isfile, isdir
from os.path import join

from .VirtualPlugin import VirtualPlugin
from ..PluginExceptions import PluginConfigError, BadPluginException, BadSettingException
from ...External.PyYAML import YAMLEasyLoad

class VirtualPluginInterface(object):

    """ This emulates the functionality of the PluginManager of the pipeline,
    but outside of the pipeline. It also handles loading and writing of the
    plugin configuration file. """

    def __init__(self):
        """ Constructs a new interface, for now we assume the plugins are at a
        fixed path """
        self._plugin_dir = "../../Plugins/"
        self._plugin_instances = []
        self._enabled_plugins = []
        self._overrides = {}

    def get_available_plugins(self):
        """ Returns a list of all installed plugins """
        plugins = []
        files = listdir(self._plugin_dir)
        for f in files:
            abspath = join(self._plugin_dir, f)
            if isdir(abspath) and f != "PluginPrefab":
                plugins.append(f)
        return plugins

    def _load_plugin_config(self):
        """ Loads the plugin configuration from the pipeline Config directory,
        and gets the list of enabled plugins and settings from that. """
        plugin_cfg = "../../Config/plugins.yaml"

        if not isfile(plugin_cfg):
            raise PluginConfigError("Could not find plugin config at " + plugin_cfg)

        content = YAMLEasyLoad(plugin_cfg)

        # Check if all required keys are in the yaml file
        if not "enabled" in content:
            raise PluginConfigError("Could not find key 'enabled' in plugin config")
        if not "overrides" in content:
            raise PluginConfigError("Could not find key 'overrides' in plugin config")

        # Get the list of enabled plugin ID's
        if content["enabled"]:
            self._enabled_plugins = content["enabled"]
        else:
            self._enabled_plugins = []

        # Get the list of setting overrides
        if content["overrides"]:
            self._overrides = content["overrides"]
        else:
            self._overrides = {}

    def load_plugins(self):
        """ Loads all plugins into memory """
        self._load_plugin_config()

        plugin_ids = self.get_available_plugins()

        for plugin in plugin_ids:

            # Try loading the plugin, and see what happens
            try:
                plugin_instance = self._load_plugin(plugin)
            except BadPluginException as msg:
                print("Bad plugin", plugin)
                print(msg)
                continue
            except BadSettingException as msg:
                print("Bad setting for", plugin)
                print(msg)
                continue

            # Try applying the overrides, and see what happens
            try:
                plugin_instance.consume_overrides(self._overrides)
            except BadSettingException as msg:
                print("Error applying overrides, bad setting")
                print(msg)
                continue

            self._plugin_instances.append(plugin_instance)

    def reset_plugin_settings(self, plugin_id):
        """ Resets all settings of a given plugin """

        # Need a copy to iterate
        for key in list(self._overrides.keys()):
            if key.startswith(plugin_id + "."):
                del self._overrides[key]

    def is_plugin_enabled(self, plugin_id):
        """ Returns wheter a plugin is currently enabled """
        return plugin_id in self._enabled_plugins
            
    def set_plugin_state(self, plugin_id, state):
        """ Sets wheter a plugin is enabled or not """
        if not state and plugin_id in self._enabled_plugins:
            self._enabled_plugins.remove(plugin_id)

        if state and plugin_id not in self._enabled_plugins:
            self._enabled_plugins.append(plugin_id)

    def get_plugin_by_id(self, plugin_id):
        """ Returns a plugin instance by a given id """
        for plugin in self._plugin_instances:
            if plugin.get_id() == plugin_id:
                return plugin
        return None

    def get_plugin_instances(self):
        """ Returns a list of all plugin instances """
        return self._plugin_instances

    def unload_plugins(self):
        """ Unloads all plugins """
        self._plugin_instances = []

    def _load_plugin(self, plugin_id):
        """ Internal method to load a plugin into memory """
        instance = VirtualPlugin()
        instance.load(plugin_id)
        return instance

    def update_setting(self, plugin_id, setting_id, new_value):
        """ Updates a plugin setting """
        plugin = self.get_plugin_by_id(plugin_id)
        setting = plugin.get_config().get_setting_handle(setting_id)
        setting.set_value(new_value)
        override_key = plugin_id + "." + setting_id
        self._overrides[override_key] = setting.value

    def write_configuration(self):
        """ Writes the plugin configuration """
        yaml = "\n\n"
        yaml+= "# This file was autogenerated by the Plugin Configurator\n"
        yaml+= "# Please avoid editing this file manually, instead use \n"
        yaml+= "# the Plugin Configurator located at Toolkit/PluginConfigurator/.\n"
        yaml+= "# Any comments and formattings in this file will be lost!\n"
        yaml+= "\n\n"

        # Write enabled plugins 
        yaml+= "enabled: \n"

        for plugin in self._enabled_plugins:
            yaml += "    - " + plugin + "\n"

        yaml += "\n"

        # Write overrides
        yaml += "overrides: \n"
        for override in sorted(self._overrides):
            new_value = self._overrides[override]
            yaml += "    " + override + ": " + str(new_value) + "\n"
        yaml += "\n"

        plugin_dest = "../../Config/plugins.yaml"

        with open(plugin_dest, "w") as handle:
            handle.write(yaml)

        # print("Wrote plugin configuration!")


