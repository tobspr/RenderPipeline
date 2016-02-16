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


from direct.stdpy.file import join
from .plugin_config import PluginConfig
from .plugin_exceptions import BadPluginException
from ..rp_object import RPObject

class VirtualPlugin(RPObject):

    """ This is a virtual plugin which emulates the functionality of a
    Pipeline Plugin outside of the pipeline. """

    def __init__(self, plugin_id):
        RPObject.__init__(self, "Plugin-" + str(plugin_id))
        self._plugin_id = plugin_id
        self._path = "rpcore/plugins/"

    def set_plugin_path(self, pth):
        """ Sets the path of the plugin """
        self._path = pth

    def load(self):
        """ Loads the virtual plugin"""
        self._config_pth = join(self._path, "config.yaml")
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
