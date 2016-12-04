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

from panda3d.core import PTAInt

from rpcore.render_stage import RenderStage


class TemporalAAStage(RenderStage):

    """ This stage performs the temporal antialiasing resolve """

    required_inputs = []
    required_pipes = ["ShadedScene", "GBuffer", "CombinedVelocity", "PreviousFrame::TemporalAAPostResolve[RGBA8]"]

    def __init__(self, pipeline):
        RenderStage.__init__(self, pipeline)

    @property
    def produced_pipes(self):
        return {
            "ShadedScene": self.post_sharpen_target.color_tex,
            "TemporalAAPostResolve": self.resolve_target.color_tex
        }

    def create(self):
        self.resolve_target = self.create_target("TAA-Resolve")
        self.resolve_target.add_color_attachment()
        self.resolve_target.prepare_buffer()

        self.post_sharpen_target = self.create_target("TAA-Sharpen")
        self.post_sharpen_target.add_color_attachment()
        self.post_sharpen_target.prepare_buffer()
        self.post_sharpen_target.set_shader_input("SourceTex", self.resolve_target.color_tex)

    def reload_shaders(self):
        self.resolve_target.shader = self.load_plugin_shader("resolve_aa.frag.glsl")
        self.post_sharpen_target.shader = self.load_plugin_shader("sharpen_aa.frag.glsl")
