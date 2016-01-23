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

import re

from direct.stdpy.file import listdir, isfile, isdir, join, open

from ..Util.DebugObject import DebugObject
from .PluginExceptions import PluginConfigError
from ..External.PyYAML import YAMLEasyLoad

class BasePluginInterface(DebugObject):

    """ This is the interface which manages loading and parsing the plugin
    configurations. It also handles writing of the plugin configuration file. """

    def __init__(self):
        """ Constructs a new interface"""
        DebugObject.__init__(self)
        self._base_dir = "../../"
        self._plugin_instances = []
        self._enabled_plugins = []
        self._overrides = {}
        self._valid_name_regexp = re.compile('^[a-zA-Z0-9_]+$')

    def get_plugin_handle(self, plugin_id):
        """ Abstract method, to be implemented by subclasses """
        raise NotImplementedError()

    def get_plugin_instances(self):
        """ Abstract method, to be implemented by subclasses """
        raise NotImplementedError()

    def load_plugins(self):
        """ Abstract method, to be implemented by subclasses """
        raise NotImplementedError()

    def has_plugin_handle(self, plugin):
        """ Checks whether a handle for the given plugin exists """
        return self.get_plugin_handle(plugin) is not None

    def set_base_dir(self, pth):
        """ Sets the path of the plugin directory, in this directory the
        PluginInterface expects the Plugins/ folder to be located. """
        self._base_dir = pth

    def get_available_plugins(self):
        """ Returns a list of all installed plugins, no matter if they are
        enabled or not. This also does no check if the plugin names are valid. """
        plugins = []
        files = listdir(join(self._base_dir, "Plugins"))
        for fname in files:
            abspath = join(self._base_dir, "Plugins", fname)
            if isdir(abspath) and fname not in ["PluginPrefab"]:
                plugins.append(fname)
        return plugins

    def get_overrides(self):
        """ Returns a handle to the dictionary of overrides, which store the
        setting-values of the plugins """
        return self._overrides

    def disable_plugin(self, plugin_id):
        """ Removes a plugin from the list of enabled plugins, this has no effect
        until write_configuration() was called. """
        self._enabled_plugins.remove(plugin_id)

    def load_plugin_config(self):
        """ Loads the plugin configuration from the pipeline Config directory,
        and gets the list of enabled plugins and settings from that. """
        plugin_cfg = "$$Config/plugins.yaml"

        if not isfile(plugin_cfg):
            raise PluginConfigError("Could not find plugin config at " + plugin_cfg)

        content = YAMLEasyLoad(plugin_cfg)

        if content is None:
            raise PluginConfigError("Plugin config is empty!")

        # Check if all required keys are in the yaml file
        if "enabled" not in content:
            raise PluginConfigError("Could not find key 'enabled' in plugin config")
        if "overrides" not in content:
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

    def reset_plugin_settings(self, plugin_id):
        """ Resets all settings of a given plugin, this has no effect until
        write_configuration() was called. """
        for key in list(self._overrides.keys()): # Need a copy to iterate
            if key.startswith(plugin_id + "."):
                del self._overrides[key]

    def is_plugin_enabled(self, plugin_id):
        """ Returns whether a plugin is currently enabled """
        return plugin_id in self._enabled_plugins

    def get_enabled_plugins(self):
        """ Returns the list of enabled plugin-ids """
        return self._enabled_plugins

    def set_plugin_state(self, plugin_id, state):
        """ Sets whether a plugin is enabled or not. This has no effect until
        write_configuration() is called """
        if not state and plugin_id in self._enabled_plugins:
            self._enabled_plugins.remove(plugin_id)

        if state and plugin_id not in self._enabled_plugins:
            self._enabled_plugins.append(plugin_id)

    def write_configuration(self):
        """ Writes the plugin configuration """
        yaml = "\n\n"
        yaml += "# This file was autogenerated by the Plugin Configurator.\n"
        yaml += "# Please avoid editing this file manually, instead use the\n"
        yaml += "# Plugin Configurator located at Toolkit/PluginConfigurator/.\n"
        yaml += "# Any comments and formattings in this file will be lost!\n"
        yaml += "\n\n"

        # Write enabled plugins
        yaml += "enabled:\n"

        for plugin in self._enabled_plugins:
            yaml += "    - " + plugin + "\n"

        yaml += "\n"

        # Write overrides
        yaml += "overrides:\n"
        for override in sorted(self._overrides):
            new_value = self._overrides[override]
            yaml += "    " + override + ": " + str(new_value) + "\n"
        yaml += "\n"

        plugin_dest = "$$Config/plugins.yaml"

        with open(plugin_dest, "w") as handle:
            handle.write(yaml)

