

from os.path import join, isfile
from .PluginConfig import PluginConfig
from .PluginExceptions import BadPluginException
from ..Util.DebugObject import DebugObject

class VirtualPlugin(DebugObject):

    """ This is a virtual plugin which emulates the functionality of a
    Pipeline Plugin outside of the pipeline. """

    def __init__(self, plugin_id):
        DebugObject.__init__(self, "Plugin-" + str(plugin_id))
        self._plugin_id = plugin_id
        self._path = "../../Plugins/"

    def set_plugin_path(self, pth):
        """ Sets the path of the plugin """
        self._path = pth

    def load(self):
        """ Loads the virtual plugin"""
        self._config_pth = join(self._path, "config.yaml")

        if not isfile(self._config_pth):
            raise BadPluginException("Missing file " + self._config_pth)

        self._config = PluginConfig()

        try:
            self._config.load(self._config_pth)
        except Exception as msg:
            self.warn("Plugin", self._plugin_id, "failed to load config.yaml:")
            self.warn(msg)
            raise BadPluginException(msg)

    def apply_overrides(self, overrides):
        """ Removes all keys from the dictionary which belong to this
        plugin and applies them to the settings """
        self._config.apply_overrides(self.get_id(), overrides)

    def get_name(self):
        """ Returns the name of the virtual plugin """
        return self._config.get_name()

    def get_config(self):
        """ Returns the PluginConfig of the virtual plugin """
        return self._config

    def get_id(self):
        """ Returns the ID of the virtual plugin """
        return self._plugin_id
