

from ..Globals import Globals
from direct.gui.DirectButton import DirectButton
import direct.gui.DirectGuiGlobals as DGG

class BetterButton:

    def __init__(self, parent, x, y, text, callback=None, callbackArgs=None):

        if callbackArgs is None:
            callbackArgs = []

        w = 50

        self.node = DirectButton(text=text, parent=parent,pressEffect=1, 
            command=callback, extraArgs=callbackArgs, scale=1, pos=(x+w,1,-y - 15),
            frameSize=(-w,w,-15,15), text_fg=(1,1,1,1), frameColor=(0.1,0.1,0.1,1.0),
            text_font=Globals.font, text_pos=(0,-4), text_scale=14)
        self.node.bind(DGG.ENTER, self.onMouseOver)
        self.node.bind(DGG.EXIT, self.onMouseOut)

    def onMouseOver(self, coords):
        self.node["frameColor"] = (0.0,0.0,0.0,1.0)

    def onMouseOut(self, coords):
        self.node["frameColor"] = (0.1,0.1,0.1,1.0)

