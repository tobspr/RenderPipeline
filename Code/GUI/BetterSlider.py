

from direct.gui.DirectSlider import DirectSlider


class BetterSlider:

    def __init__(self, x, y, parent, size=100,callback=None, extraArgs=None):
        print "Init better slider"

        if extraArgs is None:
            extraArgs = []

        self.node = DirectSlider(pos=(size + x, 1, -y), parent=parent,
                                 range=(0, 100), value=50, pageSize=1, scale=size,
                                 command=callback, extraArgs=extraArgs)

    def getValue(self):
        return self.node["value"]