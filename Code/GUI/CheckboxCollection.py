
from ..DebugObject import DebugObject

import direct.gui.DirectGuiGlobals as DGG


class CheckboxCollection(DebugObject):

    def __init__(self):
        DebugObject.__init__(self, "CheckboxCollection")
        self.items = []

    def add(self, chb):
        if chb.collection is not None:
            self.error(
                "Can't add checkbox as it already belongs to another collection")
            return

        chb._setCollection(self)
        self.items.append(chb)

    def _changed(self, chb):
        for item in self.items:
            if item is not chb:
                item._setChecked(False)
                item._node["state"] = DGG.NORMAL
