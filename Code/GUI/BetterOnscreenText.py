
from panda3d.core import Vec2, Vec3, TextNode, Vec4
from direct.gui.OnscreenText import OnscreenText

from ..Globals import Globals
from ..DebugObject import DebugObject


class BetterOnscreenText(DebugObject):

    """ Simple wrapper arround OnscreenText, providing a simpler interface
    and better visuals """

    def __init__(self, text="", parent=None, x=0, y=0, size=10, align="left",
                 color=None, mayChange=False):
        DebugObject.__init__(self, "BetterOnscreenText")

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
            align=alignMode, fg=Vec4(color.x, color.y, color.z, 1.0),
            font=Globals.font, mayChange=mayChange)

    def getInitialPos(self):
        """ Returns the initial position of the text. This can be used for
        animations """
        return self.initialPos

    def posInterval(self, *args, **kwargs):
        """ Returns a pos interval, this is a wrapper arround
        NodePath.posInterval """
        return self._node.posInterval(*args, **kwargs)
