

import collections
from Util.DebugObject import DebugObject

from direct.stdpy.file import listdir

class DayTime(DebugObject):

    """ This class manages the time of day. It stores and controls the  settings
    which change over the time of day, and also handles loading and saving
    of them """

    def __init__(self):
        DebugObject.__init__(self)
        self._settings = collections.OrderedDict()
        self._interface = VirtualPluginInterface()

    def load(self):
        """ Loads all daytime settings and overrides """
        





