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

from panda3d.core import Camera

from rpcore.globals import Globals
from rpcore.render_stage import RenderStage


class ForwardPrepassStage(RenderStage):

    """ Forward prepass stage, which allocates the light tiles so we can
    use the lights in the shader later on """

    required_inputs = []
    required_pipes = ["FlaggedCells", "SceneDepth"]

    def create(self):
        self.forward_cam = Camera("ForwardPrepassCam")
        self.forward_cam.set_lens(Globals.base.camLens)
        self.forward_cam_np = Globals.base.camera.attach_new_node(self.forward_cam)

        self.target = self.create_target("ForwardPrepass")
        self.target.prepare_render(self.forward_cam_np)
        self._pipeline.tag_mgr.register_camera("forward_prepass", self.forward_cam)

    def set_shader_input(self, name, value, *args):
        Globals.base.render.set_shader_input(name, value, *args)
        RenderStage.set_shader_input(self, name, value, *args)

