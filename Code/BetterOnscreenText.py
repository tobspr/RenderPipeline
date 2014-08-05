
from panda3d.core import Vec2, Vec3, TextNode, Vec4
from DebugObject import DebugObject
from direct.gui.OnscreenText import OnscreenText


class BetterOnscreenText(DebugObject):

    def __init__(self, text="", parent=None, x=0, y=0, size=10, align="left", color=None):
        DebugObject.__init__(self, "BOnscreenText")

        if color is None:
            color = Vec3(1)

        alignMode = TextNode.ALeft

        if align == "center":
            alignMode = TextNode.ACenter
        elif align == "right":
            alignMode = TextNode.ARight

        self.initialPos = Vec2(x, -y)

        self._node = OnscreenText(
            text=text, parent=parent, pos=self.initialPos, scale=size, 
            align=alignMode, fg=Vec4(color.x, color.y, color.z, 1.0))

    def getInitialPos(self):
        return self.initialPos

    def posInterval(self, *args, **kwargs):
        return self._node.posInterval(*args, **kwargs)
