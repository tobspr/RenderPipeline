

from ..DebugObject import DebugObject
from ..Globals import Globals
from BetterOnscreenText import BetterOnscreenText

from panda3d.core import Vec3
from direct.gui.DirectFrame import DirectFrame


class UIWindow(DebugObject):

    """ This is a simple wrapper arround DirectFrame, which simulates a window,
    including a title """

    def __init__(self, title, w=100, h=100, parent=None):
        DebugObject.__init__(self, "UIWindow")

        if parent is None:
            parent = Globals.base.pixel2d

        self.node = parent.attachNewNode("Window-" + title)
        self.parent = parent

        self.bgFrame = DirectFrame(parent=self.node,
                                   frameColor=(0.2, 0.2, 0.2, 0.9),
                                   frameSize=(0, w, -h, 0))  # state=DGG.NORMAL

        self.titleFrame = DirectFrame(parent=self.node,
                                      frameColor=(0.35, 0.56, 0.19, 0.9),
                                      frameSize=(0, w, -40, 0))
        self.titleText = BetterOnscreenText(text=title, x=10, y=25,
                                            parent=self.titleFrame,
                                            color=Vec3(1), size=15)
        self.contentNode = self.node.attachNewNode("Content")
        self.contentNode.setPos(0, 0, -60)

    def getNode(self):
        """ Returns the window node """
        return self.node

    def getContentNode(self):
        """ Returns the content node, you should reparent your content to this
        node """
        return self.contentNode
