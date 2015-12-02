
import direct.gui.DirectGuiGlobals as DGG
from direct.gui.DirectSlider import DirectSlider

from ..Util.DebugObject import DebugObject

class BetterSlider(DebugObject):

    """ This is a simple wrapper around DirectSlider, providing a simpler
    interface """

    def __init__(self, x=0, y=0, parent=None, size=100, min_value=0,
                 max_value=100, value=50, page_size=1, callback=None,
                 extra_args=None):
        """ Inits the slider """
        DebugObject.__init__(self)
        if extra_args is None:
            extra_args = []

        # Scale has to be 2.0, otherwise there will be an error.
        self._node = DirectSlider(pos=(size * 0.5 + x, 1, -y), parent=parent,
                                  range=(min_value, max_value), value=value,
                                  pageSize=page_size, scale=2.0,
                                  command=callback, extraArgs=extra_args,
                                  frameColor=(0.04, 0.04, 0.04, 0.8),
                                  frameSize=(-size * 0.25, size * 0.25, -5, 5),
                                  thumb_frameColor=(0.35, 0.53, 0.2, 1.0),
                                  thumb_frameSize=(-2.5, 2.5, -5.0, 5.0),
                                  thumb_relief=DGG.FLAT, relief=DGG.FLAT)

    def get_value(self):
        """ Returns the currently assigned value """
        return self._node["value"]
