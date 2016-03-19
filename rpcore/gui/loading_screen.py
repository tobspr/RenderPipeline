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

from panda3d.core import Shader, Vec4, Vec3

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
        self.pipeline = pipeline

    def create(self):
        """ Creates the gui components """

        screen_w, screen_h = Globals.base.win.get_x_size(), Globals.base.win.get_y_size()

        self.fullscreen_node = Globals.base.pixel2dp.attach_new_node(
            "PipelineDebugger")
        self.fullscreen_node.set_bin("fixed", 10)
        self.fullscreen_node.set_depth_test(False)

        scale_w = screen_w / 1920.0
        scale_h = screen_h / 1080.0
        scale = max(scale_w, scale_h)

        self.fullscreen_bg = Sprite(
            image="/$$rp/data/gui/loading_screen_bg.png",
            x=(screen_w-1920.0*scale)//2, y=(screen_h-1080.0*scale)//2, w=int(1920 * scale), h=int(1080 * scale),
            parent=self.fullscreen_node, near_filter=False)

        self.loading_images = Globals.loader.load_texture("/$$rp/data/gui/loading_screen_anim.png")
        self.loading_bg = Sprite(parent=self.fullscreen_node, image=self.loading_images,
            x=(screen_w-420)//2, y=(screen_h-420)//2 + 50, w=420, h=420)

        loading_shader = Shader.load(Shader.SL_GLSL,
            "/$$rp/rpcore/shader/default_gui_shader.vert.glsl",
            "/$$rp/rpcore/shader/loading_anim.frag.glsl")
        self.loading_bg._node.set_shader(loading_shader)
        self.loading_bg.set_shader_input("frameIndex", 0)

        for _ in range(2):
            Globals.base.graphicsEngine.render_frame()

        self.update_task = Globals.base.taskMgr.add(self.update, "updateLoadingScreen")

    def update(self, task=None):
        """ Updates the loading screen """
        anim_duration = 4.32
        self.loading_bg.set_shader_input("frameIndex", int(Globals.clock.get_frame_time() / anim_duration * 144.0) % 144)
        if task:
            return task.cont

    def remove(self):
        """ Removes the loading screen """
        Globals.base.taskMgr.doMethodLater(8.0, self.cleanup, "cleanupLoadingScreen")
        # self.fullscreen_node.colorScaleInterval(3.9, Vec4(1, 1, 1, 0), Vec4(1), blendType="easeIn").start()

    def cleanup(self, task):
        """ Internal method to cleanup the loading screen"""
        Globals.base.taskMgr.remove(self.update_task)

        # Free the used resources
        self.fullscreen_bg._node["image"].get_texture().release_all()
        self.loading_bg._node["image"].get_texture().release_all()
        self.fullscreen_node.remove_node()

        return task.done
