from __future__ import division

from panda3d.core import Vec3, Vec2, RenderState, TransformState
from direct.gui.DirectFrame import DirectFrame
from direct.gui.DirectGuiBase import DGG

from .BetterOnscreenImage import BetterOnscreenImage
from .BetterOnscreenText import BetterOnscreenText

from ..Util.DebugObject import DebugObject
from ..Globals import Globals




class EmptyLoadingScreen(object):

    """ This loading screen is used when no loading screen is specified in the
    pipeline """

    def __getattr__(self, *args, **kwargs):
        """ Always return a lambda no matter which attribute is queried """
        return lambda *args, **kwargs: None

class PipelineLoadingScreen(DebugObject):

    """ This is the default loading screen used by the pipeline"""

    def __init__(self, pipeline):
        DebugObject.__init__(self)
        self.debug("Creating loading screen ..")
        self._pipeline = pipeline

    def create(self):
        """ Creates the gui components """

        sw, sh = Globals.base.win.get_x_size(), Globals.base.win.get_y_size()


        self._fullscreen_node = Globals.base.pixel2dp.attach_new_node(
            "PipelineDebugger")
        self._fullscreen_node.set_bin("fixed", 10)
        self._fullscreen_node.set_depth_test(False)

        self._fullscreen_bg = BetterOnscreenImage(
            image="Data/GUI/LoadingScreen/Background.png",
            x=0, y=0, w=sw, h=sh, parent=self._fullscreen_node)

        # self._bottom_border = DirectFrame(pos=(0, 0, -sh+150),
        #     parent=self._fullscreen_node, frameColor=(0.78, 0.78, 0.78, 1.0),
        #     frameSize=(-5000, 5000, 0, -2))

        self._logo = BetterOnscreenImage(
            image="Data/GUI/Generic/RPLogoText.png",
            parent=self._fullscreen_node)

        lw, lh = self._logo.get_width(), self._logo.get_height()
        self._logo.set_pos((sw - lw) // 2, (sh - lh) // 2)

        self._loading_text = BetterOnscreenImage(
            image="Data/GUI/LoadingScreen/LoadingText.png",
            parent=self._fullscreen_node)
        lw, lh = self._loading_text.get_width(), self._loading_text.get_height()
        self._loading_text.set_pos((sw - lw) // 2, sh - 80)


        for i in range(3):
            Globals.base.graphicsEngine.render_frame()

    def remove(self):
        self._fullscreen_node.remove_node()
