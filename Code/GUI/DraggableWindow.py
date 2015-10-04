

from panda3d.core import Vec2, TransparencyAttrib
from direct.gui.DirectFrame import DirectFrame
from direct.gui.DirectButton import DirectButton
from direct.gui.DirectGui import DGG

from ..Util.DebugObject import DebugObject
from ..Globals import Globals
from BetterOnscreenText import BetterOnscreenText


class DraggableWindow(DebugObject):

    """ This is a simple draggable but not resizeable window """

    def __init__(self, width=800, height=500, title="Window"):
        DebugObject.__init__(self, "Window-" + title)
        self._width = width
        self._height = height
        self._title = title
        self._visible = True
        self._pos = Vec2((Globals.base.win.get_x_size() - self._width) / 2,
                         (Globals.base.win.get_y_size() - self._height) / 2)
        self._dragging = False
        self._drag_offset = Vec2(0)

    def set_title(self, title):
        """ Sets the window title """
        self._title = title
        self._window_title.set_text(title)

    def show(self):
        """ Shows the window """
        self._visible = True
        self._node.show()

    def hide(self):
        """ Hides the window """
        self._visible = False
        self._stop_drag()
        self._node.hide()

    def remove(self):
        """ Removes the window from the scene graph. You should still delete the
        instance """
        self._stop_drag()
        self._node.remove_node()

    def _create_components(self):
        """ Creates the window components """
        parent = Globals.base.pixel2d
        self._node = parent.attach_new_node("Window")
        self._node.set_pos(self._pos.x, 1, -self._pos.y)
        border_px = 4
        self._border_frame = DirectFrame(pos=(0, 1, 0),
                                         frameSize=(-border_px,
                                                    self._width + border_px,
                                                    border_px,
                                                    -self._height - border_px),
                                         frameColor=(0.34, 0.564, 0.192, 1.0),
                                         parent=self._node, state=DGG.NORMAL)
        self._background = DirectFrame(pos=(0, 1, 0),
                                       frameSize=(0, self._width,
                                                  0, -self._height),
                                       frameColor=(0.1, 0.1, 0.1, 1),
                                       parent=self._node)
        self._title_bar = DirectFrame(pos=(0, 1, 0),
                                      frameSize=(0, self._width, 0, -40),
                                      frameColor=(0.15, 0.15, 0.15, 1),
                                      parent=self._node, state=DGG.NORMAL)
        self._window_title = BetterOnscreenText(parent=self._node, x=10, y=26,
                                                text=self._title, size=18)
        self._btn_close = DirectButton(relief=False, pressEffect=1,
                                       pos=(self._width - 20, 1, -20),
                                       scale=(14, 1, 14), parent=self._node,
                                       image="Data/GUI/CloseWindow.png")

        # Init bindings
        self._btn_close.set_transparency(TransparencyAttrib.M_alpha)
        self._btn_close.bind(DGG.B1CLICK, self._request_close)
        self._title_bar.bind(DGG.B1PRESS, self._start_drag)
        self._title_bar.bind(DGG.B1RELEASE, self._stop_drag)

    def _start_drag(self, evt=None):
        """ Gets called when the user starts dragging the window """
        self._dragging = True
        self._node.detach_node()
        self._node.reparent_to(Globals.base.pixel2d)
        Globals.base.taskMgr.add(self._on_tick, "UIWindowDrag",
                                 uponDeath=self._stop_drag)
        self._drag_offset = self._pos - self._get_mouse_pos()

    def _request_close(self, evt=None):
        """ This method gets called when the close button gets clicked """
        self.hide()

    def _stop_drag(self, evt=None):
        """ Gets called when the user stops dragging the window """
        Globals.base.taskMgr.remove("UIWindowDrag")
        self._dragging = False

    def _get_mouse_pos(self):
        """ Internal helper function to get the mouse position """
        mx, my = (Globals.base.win.get_pointer(0).get_x(),
                  Globals.base.win.get_pointer(0).get_y())
        return Vec2(mx, my)

    def _set_pos(self, pos):
        """ Moves the window to the specified position """
        self._pos = pos
        self._pos.x = max(self._pos.x, -self._width + 100)
        self._pos.y = max(self._pos.y, 25)
        self._pos.x = min(self._pos.x, Globals.base.win.get_x_size() - 100)
        self._pos.y = min(self._pos.y, Globals.base.win.get_y_size() - 50)
        self._node.set_pos(self._pos.x, 1, -self._pos.y)

    def _on_tick(self, task):
        """ Task which updates the window while being dragged """
        self._set_pos(self._get_mouse_pos() + self._drag_offset)
        return task.cont
