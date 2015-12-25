
from panda3d.core import Texture, TransparencyAttrib
from direct.gui.DirectCheckBox import DirectCheckBox
import direct.gui.DirectGuiGlobals as DGG

from ..Util.DebugObject import DebugObject
from ..Globals import Globals


class BetterCheckbox(DebugObject):

    """ This is a wrapper around DirectCheckBox, providing a simpler interface
    and better visuals """

    def __init__(self, parent=None, x=0, y=0, callback=None, extra_args=None,
                 radio=False, expand_width=100, checked=False):
        DebugObject.__init__(self)

        prefix = "Checkbox" if not radio else "Radiobox"
        checked_img = Globals.loader.loadTexture(
            "Data/GUI/OnscreenDebugger/" + prefix + "Checked.png")
        unchecked_img = Globals.loader.loadTexture(
            "Data/GUI/OnscreenDebugger/" + prefix + "Default.png")

        # Set near filter, otherwise textures look like crap
        for tex in [checked_img, unchecked_img]:
            tex.set_minfilter(Texture.FT_linear)
            tex.set_magfilter(Texture.FT_linear)
            tex.set_anisotropic_degree(0)
            tex.set_wrap_u(Texture.WM_clamp)
            tex.set_wrap_v(Texture.WM_clamp)

        self._node = DirectCheckBox(
            parent=parent, pos=(x + 11, 1, -y - 8), scale=(10 / 2.0, 1, 10 / 2.0),
            checkedImage=checked_img, uncheckedImage=unchecked_img,
            image=unchecked_img, extraArgs=extra_args, state=DGG.NORMAL,
            relief=DGG.FLAT, command=self._update_status)

        self._node["frameColor"] = (0, 0, 0, 0)
        self._node["frameSize"] = (-2.6, 2 + expand_width / 7.5, -2.35, 2.35)
        self._node.set_transparency(TransparencyAttrib.M_alpha)

        self._callback = callback
        self._extra_args = extra_args
        self._collection = None

        if checked:
            self.set_checked(True, False)

    def set_collection(self, coll):
        """ Internal method to add a checkbox to a checkbox collection, this
        is used for radio-buttons """
        self._collection = coll

    def get_collection(self):
        """ Returns a handle to the assigned checkbox collection, or None
        if no collection was assigned """
        return self._collection

    def _update_status(self, status, *args):
        """ Internal method when another checkbox in the same radio group
        changed it's value """

        if not status and self._collection:
            self._node.commandFunc(None)
            return

        if self._collection:
            if status:
                self._collection._changed(self)
                # A radio box can't be unchecked
                # self._node["state"] = DGG.DISABLED

        if self._callback is not None:
            self._callback(*([status] + self._extra_args))

    def set_checked(self, val, do_callback=True):
        """ Internal method to check/uncheck the checkbox """
        self._node["isChecked"] = val

        if val:
            self._node['image'] = self._node['checkedImage']
        else:
            self._node['image'] = self._node['uncheckedImage']

        if do_callback and self._callback is not None:
            self._callback(*([val] + self._extra_args))
