

from os.path import join, isdir, isfile
from Code.PluginInterface.PluginConfig import PluginConfig

class BadPluginException(Exception):
    pass

class VirtualPlugin(object):

    def __init__(self):
        pass

    def load(self, plugin_id):
        """ Loads the virtual plugin from a given id """
        self._plugin_id = plugin_id
        self._plugin_pth = join("../../Plugins/", self._plugin_id)
        self._config_pth = join(self._plugin_pth, "config.yaml")

        if not isfile(self._config_pth):
            raise BadPluginException("Missing file " + self._config_pth)

        self._load_config()

    def _load_config(self):
        """ Loads the plugin config """

        self._config = PluginConfig()
        self._config.load(self._config_pth)

    def get_name(self):
        return self._config.get_name()

    def get_config(self):
        return self._config

    def get_id(self):
        return self._plugin_id
