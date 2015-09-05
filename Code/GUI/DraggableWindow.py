

from panda3d.core import Vec2, TransparencyAttrib
from direct.gui.DirectFrame import DirectFrame
from direct.gui.DirectButton import DirectButton
from direct.gui.DirectGui import DGG

from ..Util.DebugObject import DebugObject
from ..Util.FunctionDecorators import protected
from ..Globals import Globals
from BetterOnscreenText import BetterOnscreenText



class DraggableWindow(DebugObject):

    """ This is a simple draggable but not resizeable window """

    def __init__(self, width=800, height=500, title="Window"):
        DebugObject.__init__(self, "Window-" + title)
        self.width = width
        self.height = height
        self.title = title
        self.visible = True
        self.pos = Vec2( (Globals.base.win.getXSize()-self.width)/2, (Globals.base.win.getYSize()-self.height)/2)
        self.dragging = False
        self.dragOffset = Vec2(0)

    def setTitle(self, title):
        """ Sets the window title """
        self.title = title
        self.windowTitle.setText(title)

    def show(self):
        """ Shows the window """
        self.visible = True
        self._node.show()

    def hide(self):
        """ Hides the window """
        self.visible = False
        self._stopDrag()
        self._node.hide()

    def remove(self):
        """ Removes the window from the scene graph. You should still delete the
        instance """
        self._stopDrag()
        self._node.removeNode()

    @protected
    def _createComponents(self):
        """ Creates the window components """
        parent = Globals.base.pixel2d
        self._node = parent.attachNewNode("Window")
        self._node.setPos(self.pos.x, 1, -self.pos.y)
        borderSize = 4
        self.borderFrame = DirectFrame(pos=(0, 1, 0), frameSize=(-borderSize, self.width + borderSize, borderSize, -self.height - borderSize), frameColor=(0.34, 0.564, 0.192, 1.0), parent=self._node, state=DGG.NORMAL)
        self.background = DirectFrame(pos=(0, 1, 0), frameSize=(0, self.width, 0, -self.height),
            frameColor=(0.1, 0.1, 0.1, 1), parent=self._node)
        self.titleBar = DirectFrame(pos=(0, 1, 0), frameSize=(0, self.width, 0, -40),
            frameColor=(0.15, 0.15, 0.15, 1), parent=self._node, state=DGG.NORMAL)
        self.windowTitle = BetterOnscreenText(parent=self._node, x=10, y=26, text=self.title, size=18)
        self.btnClose = DirectButton(relief=False, pressEffect=1, pos=(self.width - 20, 1, -20), scale=(14, 1, 14), parent=self._node, image="Data/GUI/CloseWindow.png")
        self.btnClose.setTransparency(TransparencyAttrib.MAlpha)
        self.titleBar.bind(DGG.B1PRESS, self._startDrag)
        self.titleBar.bind(DGG.B1RELEASE, self._stopDrag)
        self.btnClose.bind(DGG.B1CLICK, self._requestClose)

    @protected
    def _startDrag(self, evt=None):
        """ Gets called when the user starts dragging the window """
        self.dragging = True
        self._node.detachNode()
        self._node.reparentTo(Globals.base.pixel2d)
        Globals.base.taskMgr.add(self._onTick, "UIWindowDrag", uponDeath=self._stopDrag)
        self.dragOffset = self.pos - self._getMousePos()

    @protected
    def _requestClose(self, evt=None):
        """ This method gets called when the close button gets clicked """
        self.hide()

    @protected
    def _stopDrag(self, evt=None):
        """ Gets called when the user stops dragging the window """
        Globals.base.taskMgr.remove("UIWindowDrag")
        self.dragging = False

    @protected
    def _getMousePos(self):
        """ Internal helper function to get the mouse position """
        mx, my = Globals.base.win.getPointer(0).getX(), Globals.base.win.getPointer(0).getY()
        return Vec2(mx, my)

    @protected
    def _setPos(self, pos):
        """ Moves the window to the specified position """
        self.pos = pos
        self.pos.x = max(self.pos.x, -self.width + 100)
        self.pos.y = max(self.pos.y, 25)
        self.pos.x = min(self.pos.x, Globals.base.win.getXSize() - 100)
        self.pos.y = min(self.pos.y, Globals.base.win.getYSize() - 50)
        self._node.setPos(self.pos.x, 1, -self.pos.y)

    @protected
    def _onTick(self, task):
        """ Task which updates the window while being dragged """
        self._setPos(self._getMousePos() + self.dragOffset)
        return task.cont

