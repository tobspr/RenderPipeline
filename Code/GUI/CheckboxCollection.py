
from ..Util.DebugObject import DebugObject

import direct.gui.DirectGuiGlobals as DGG


class CheckboxCollection(DebugObject):

    """ This is a container for multiple BetterCheckboxes, controlling that
    only one checkbox of this collection is checked at one time
    (like a radio-button) """

    def __init__(self):
        DebugObject.__init__(self)
        self._items = []

    def add(self, chb):
        """ Adds a BetterCheckbox to this collection """
        if chb.get_collection() is not None:
            self.error(
                "Can't add checkbox as it already belongs "
                "to another collection!")
            return
        chb.set_collection(self)
        self._items.append(chb)

    def remove(self, chb):
        """ Removes a checkbox from this collection """
        if chb.get_collection() is not self:
            self.error(
                "Can't remove the checkbox from this collection as it is not "
                "attached to this collection!")
            return
        chb.set_collection(None)
        self._items.remove(chb)

    def _changed(self, chb):
        """ Internal callback when a checkbox got changed """
        for item in self._items:
            if item is not chb:
                item.set_checked(False)
                item._node["state"] = DGG.NORMAL
