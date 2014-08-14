
import direct.gui.DirectGuiGlobals as DGG

from direct.gui.DirectSlider import DirectSlider


class BetterSlider:

    """ This is a simple wrapper arround DirectSlider, providing a simpler
    interface and better visuals """

    def __init__(self, x, y, parent, size=100, minValue=0, maxValue=100,
                 value=50, pageSize=1, callback=None, extraArgs=None):
        if extraArgs is None:
            extraArgs = []

        # Scale has to be 2.0, otherwise there will be an error.
        self.node = DirectSlider(pos=(size * 0.5 + x, 1, -y), parent=parent,
                                 range=(minValue, maxValue), value=value,
                                 pageSize=pageSize, scale=2.0,
                                 command=callback, extraArgs=extraArgs,
                                 frameColor=(0.13, 0.13, 0.13, 0.8),
                                 frameSize=(-size * 0.25, size * 0.25, -5, 5),
                                 thumb_frameColor=(0.35, 0.53, 0.2, 1.0),
                                 thumb_frameSize=(-2.5, 2.5, -5.0, 5.0),
                                 thumb_relief=DGG.FLAT, relief=DGG.FLAT)

    def getValue(self):
        """ Returns the currently assigned value """
        return self.node["value"]
