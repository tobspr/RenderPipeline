
import direct.gui.DirectGuiGlobals as DGG

from direct.gui.DirectSlider import DirectSlider


class BetterSlider:

    def __init__(self, x, y, parent, size=100,callback=None, extraArgs=None):
        print "Init better slider"

        if extraArgs is None:
            extraArgs = []

        self.node = DirectSlider(pos=(size*0.5 + x, 1, -y), parent=parent,
                                 range=(0, 100), value=50, pageSize=1, scale=2.0,
                                 command=callback, extraArgs=extraArgs,
                                 frameColor=(0.13,0.13,0.13,0.8), frameSize=(-size*0.25,size*0.25,-5,5),
                                 thumb_frameColor=(0.35,0.53,0.2,1.0), thumb_frameSize=(-2.5,2.5,-5.0,5.0),
                                 thumb_relief=DGG.FLAT, relief=DGG.FLAT)

    def getValue(self):
        return self.node["value"]