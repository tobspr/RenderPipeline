"""

RenderPipeline

Copyright (c) 2014-2016 tobspr <tobias.springer1@gmail.com>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
 	 	    	 	
"""
from __future__ import division
from six.moves import range

from .better_onscreen_image import BetterOnscreenImage

from ..rp_object import RPObject
from ..globals import Globals

class EmptyLoadingScreen(object):

    """ This loading screen is used when no loading screen is specified in the
    pipeline """

    def __getattr__(self, *args, **kwargs):
        """ Always return a lambda no matter which attribute is queried """
        return lambda *args, **kwargs: None


class PipelineLoadingScreen(RPObject):

    """ This is the default loading screen used by the pipeline"""

    def __init__(self, pipeline):
        """ Inits the loading screen """
        RPObject.__init__(self)
        self._pipeline = pipeline

    def create(self):
        """ Creates the gui components """

        screen_w, screen_h = Globals.base.win.get_x_size(), Globals.base.win.get_y_size()

        self._fullscreen_node = Globals.base.pixel2dp.attach_new_node(
            "PipelineDebugger")
        self._fullscreen_node.set_bin("fixed", 10)
        self._fullscreen_node.set_depth_test(False)

        self._fullscreen_bg = BetterOnscreenImage(
            image="data/gui/loading_screen_bg.png",
            x=0, y=0, w=screen_w, h=screen_h, parent=self._fullscreen_node)

        self._logo = BetterOnscreenImage(
            image="data/gui/rp_logo_text.png",
            parent=self._fullscreen_node)

        logo_w, logo_h = self._logo.get_width(), self._logo.get_height()
        self._logo.set_pos((screen_w - logo_w) // 2, (screen_h - logo_h) // 2)

        self._loading_text = BetterOnscreenImage(
            image="data/gui/loading_screen_text.png",
            parent=self._fullscreen_node)
        loading_text_w = self._loading_text.get_width()
        self._loading_text.set_pos((screen_w - loading_text_w) // 2, screen_h - 80)

        for i in range(3):
            Globals.base.graphicsEngine.render_frame()

    def remove(self):
        """ Removes the loading screen """
        self._fullscreen_node.remove_node()
