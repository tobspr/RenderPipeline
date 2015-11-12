from __future__ import print_function 

from os import listdir
from os.path import isfile, isdir, join

from VirtualPlugin import VirtualPlugin, BadPluginException

class PluginInterface(object):

    def __init__(self):
        self._plugin_dir = "../../Plugins/"
        self._plugin_instances = []

    def get_available_plugins(self):
        """ Returns a list of all installed plugins """

        plugins = []
        files = listdir(self._plugin_dir)

        for f in files:
            abspath = join(self._plugin_dir, f)
            if isdir(abspath) and f != "PluginPrefab":
                plugins.append(f)

        return plugins

    def load_plugins(self):
        """ Loads all plugins into memory """
        plugin_ids = self.get_available_plugins()

        for plugin in plugin_ids:
            try:
                plugin_instance = self._load_plugin(plugin)
            except BadPluginException as msg:
                print("Bad plugin", plugin)
                print(msg)
                continue
            except Exception as msg:
                print("Unexpected exception loading", plugin)
                print(msg)
                continue

            self._plugin_instances.append(plugin_instance)

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
