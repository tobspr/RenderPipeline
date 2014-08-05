


from ..DebugObject import DebugObject
from ..Globals import Globals
from BetterOnscreenText import BetterOnscreenText

from panda3d.core import Vec3
from direct.gui.DirectFrame import DirectFrame


class UIWindow(DebugObject):

    def __init__(self, title, w=100, h=100):
        DebugObject.__init__(self, "UIWindow")

        self.node = Globals.base.pixel2d.attachNewNode("Window-" + title)
        self.bgFrame = DirectFrame(parent=self.node, frameColor=(0.2,0.2,0.2,0.98), 
            frameSize=(0, w, -h, 0))
        self.titleFrame = DirectFrame(parent=self.node, frameColor=(0.35,0.56,0.19,1.0), 
            frameSize=(0, w, -40, 0))
        self.titleText = BetterOnscreenText(text=title, x=10, y=25, parent=self.titleFrame,
            color=Vec3(1), size=15)
        self.contentNode = self.node.attachNewNode("Content")
        self.contentNode.setPos(0,0,-60)

    def getNode(self):
        return self.node

    def getContentNode(self):
        return self.contentNode

