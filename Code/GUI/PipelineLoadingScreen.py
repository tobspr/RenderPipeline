from __future__ import division
from six.moves import range

from .BetterOnscreenImage import BetterOnscreenImage

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
        """ Inits the loading screen """
        DebugObject.__init__(self)
        self._pipeline = pipeline

    def create(self):
        """ Creates the gui components """

        screen_w, screen_h = Globals.base.win.get_x_size(), Globals.base.win.get_y_size()

        self._fullscreen_node = Globals.base.pixel2dp.attach_new_node(
            "PipelineDebugger")
        self._fullscreen_node.set_bin("fixed", 10)
        self._fullscreen_node.set_depth_test(False)

        self._fullscreen_bg = BetterOnscreenImage(
            image="Data/GUI/LoadingScreen/Background.png",
            x=0, y=0, w=screen_w, h=screen_h, parent=self._fullscreen_node)

        self._logo = BetterOnscreenImage(
            image="Data/GUI/Generic/RPLogoText.png",
            parent=self._fullscreen_node)

        logo_w, logo_h = self._logo.get_width(), self._logo.get_height()
        self._logo.set_pos((screen_w - logo_w) // 2, (screen_h - logo_h) // 2)

        self._loading_text = BetterOnscreenImage(
            image="Data/GUI/LoadingScreen/LoadingText.png",
            parent=self._fullscreen_node)
        loading_text_w = self._loading_text.get_width()
        self._loading_text.set_pos((screen_w - loading_text_w) // 2, screen_h - 80)

        for i in range(3):
            Globals.base.graphicsEngine.render_frame()

    def remove(self):
        """ Removes the loading screen """
        self._fullscreen_node.remove_node()
