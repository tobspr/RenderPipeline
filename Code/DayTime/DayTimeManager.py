

import collections

from direct.stdpy.file import listdir

from ..Util.DebugObject import DebugObject
from ..PluginInterface.Virtual.VirtualPluginInterface import VirtualPluginInterface


class DayTimeManager(DebugObject):

    """ This class manages the time of day. It stores and controls the settings
    which change over the time of day, and also handles loading and saving
    of them """

    def __init__(self, interface):
        """ Constructs a new DayTime, the interface should be a handle to a 
        BasePluginInterface or any derived class of that """
        DebugObject.__init__(self)
        self._settings = collections.OrderedDict()
        self._interface = interface

    def load(self):
        """ Loads all daytime settings and overrides """

        # First, collect all possible settings
        for plugin in self._interface.get_enabled_plugins():
            handle = self._interface.get_plugin_handle(plugin)
            print(handle)




