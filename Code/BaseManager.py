

from .Util.DebugObject import DebugObject
from panda3d.core import PStatCollector

class BaseManager(DebugObject):

    """ Base class for all managers, provides utility functions like timing
    the update duration """

    def __init__(self):
        """ Inits the manager """
        self._mgr_name = self.__class__.__name__
        DebugObject.__init__(self, self._mgr_name)
        self._update_collector = PStatCollector("App:Show code:RP_UpdateManagers:" + self._mgr_name)
        assert hasattr(self, "do_update")

    def update(self):
        """ Updates the manager, this just calls the do_update() method and
        times it """
        self._update_collector.start()
        self.do_update()
        self._update_collector.stop()
