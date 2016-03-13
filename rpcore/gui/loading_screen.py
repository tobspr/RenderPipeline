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
from rplibs.six.moves import range

from rpcore.gui.sprite import Sprite

from rpcore.rpobject import RPObject
from rpcore.globals import Globals

class EmptyLoadingScreen(object):

    """ This loading screen is used when no loading screen is specified in the
    pipeline """

    def create(self):
        pass

    def remove(self):
        pass

class LoadingScreen(RPObject):

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

        scale_w = screen_w / 1920.0
        scale_h = screen_h / 1080.0
        scale = max(scale_w, scale_h)

        self._fullscreen_bg = Sprite(
            image="/$$rp/data/gui/loading_screen_bg.png",
            x=(screen_w-1920.0*scale)//2, y=(screen_h-1080.0*scale)//2, w=int(1920 * scale), h=int(1080 * scale),
            parent=self._fullscreen_node, near_filter=False)

        # self._logo = Sprite(
        #     image="/$$rp/data/gui/rp_logo_text.png",
        #     parent=self._fullscreen_node)

        # logo_w, logo_h = self._logo.get_width(), self._logo.get_height()
        # self._logo.set_pos((screen_w - logo_w) // 2, (screen_h - logo_h) // 2)

        # self._loading_text = Sprite(
        #     image="/$$rp/data/gui/loading_screen_text.png",
        #     parent=self._fullscreen_node)
        # loading_text_w = self._loading_text.get_width()
        # self._loading_text.set_pos((screen_w - loading_text_w) // 2, screen_h - 80)

        for _ in range(3):
            Globals.base.graphicsEngine.render_frame()

    def remove(self):
        """ Removes the loading screen """
        self._fullscreen_node.remove_node()

        # Free the used resources
        self._fullscreen_bg._node["image"].get_texture().release_all()
        # self._logo._node["image"].get_texture().release_all()
        # self._loading_text._node["image"].get_texture().release_all()
