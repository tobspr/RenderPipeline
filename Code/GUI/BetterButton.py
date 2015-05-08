
from direct.gui.DirectButton import DirectButton
import direct.gui.DirectGuiGlobals as DGG

from ..Globals import Globals
from ..DebugObject import DebugObject

class BetterButton(DebugObject):
  
    """ This is a wrapper arround DirectButton, providing a simpler interface
    and better visuals """

    def __init__(self, parent, x, y, text, width=50, callback=None,
                 callbackArgs=None):

        DebugObject.__init__(self, "BetterButton")

        if callbackArgs is None:
            callbackArgs = []

        self._node = DirectButton(text=text, parent=parent, pressEffect=1,
                                  command=callback, extraArgs=callbackArgs,
                                  scale=1, pos=(x + width, 1, -y - 15),
                                  frameSize=(-width, width, -15, 15),
                                  text_fg=(1, 1, 1, 1),
                                  frameColor=(0.1, 0.1, 0.1, 1.0),
                                  text_font=Globals.font, text_pos=(0, -4),
                                  text_scale=14)

        # Add a hover effect
        self._node.bind(DGG.ENTER, self._onMouseOver)
        self._node.bind(DGG.EXIT, self._onMouseOut)

    def _onMouseOver(self, coords):
        self._node["frameColor"] = (0.0, 0.0, 0.0, 1.0)

    def _onMouseOut(self, coords):
        self._node["frameColor"] = (0.1, 0.1, 0.1, 1.0)
