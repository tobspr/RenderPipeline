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

from panda3d.core import SamplerState, Texture, Vec4

from rpcore.render_stage import RenderStage
from rpcore.image import Image
from rpcore.util.slice_loader import load_sliced_3d_texture

class ApplyCloudsStage(RenderStage):

    """ This stage raymarchs the cloud voxel grid """

    required_pipes = ["ShadedScene", "GBuffer"]

    def __init__(self, pipeline):
        RenderStage.__init__(self, pipeline)

    @property
    def produced_pipes(self):
        return {"ShadedScene": self._target_apply_clouds.color_tex}

    def create(self):
        self._render_target = self.make_target2("RaymarchVoxels")
        self._render_target.size = -2
        self._render_target.add_color_attachment(bits=16, alpha=True)
        self._render_target.prepare_buffer()

        self._target_apply_clouds = self.make_target2("MergeWithScene")
        self._target_apply_clouds.add_color_attachment(bits=16)
        self._target_apply_clouds.prepare_buffer()

        self._target_apply_clouds.set_shader_input(
            "CloudsTex", self._render_target.color_tex)

    def set_shaders(self):
        self._target_apply_clouds.shader = self.load_plugin_shader("apply_clouds.frag.glsl")
        self._render_target.shader = self.load_plugin_shader("render_clouds.frag.glsl")
