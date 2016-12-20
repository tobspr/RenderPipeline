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

from panda3d.core import LVecBase2i

from rpcore.render_stage import RenderStage


class GodrayStage(RenderStage):

    """ This stage computes and renders the suns godrays """

    required_inputs = []
    required_pipes = ["ShadedScene", "GBuffer", "PreviousFrame::PostGodrayResolve[R16]"]

    @property
    def produced_pipes(self):
        return {
            "ShadedScene": self.target_merge.color_tex,
            "PostGodrayResolve": self.target_resolve.color_tex
        }

    def create(self):

        self.target_mask = self.create_target("MaskGodrays")
        self.target_mask.size = "50%"
        self.target_mask.add_color_attachment(bits=(1, 0, 0, 0))
        self.target_mask.prepare_buffer()

        self.target = self.create_target("ComputeGodrays")
        self.target.size = "50%"
        self.target.add_color_attachment(bits=(16, 0, 0, 0))
        self.target.prepare_buffer()
        self.target.set_clear_color(0)
        self.target.set_shader_input("SunMask", self.target_mask.color_tex)

        self.target_blur_v = self.create_target("BlurGodraysV")
        self.target_blur_v.size = "50%"
        self.target_blur_v.add_color_attachment(bits=(16, 0, 0, 0))
        self.target_blur_v.prepare_buffer()

        self.target_blur_v.set_shader_input("direction", LVecBase2i(1, 0))
        self.target_blur_v.set_shader_input("SourceTex", self.target.color_tex)

        self.target_blur_h = self.create_target("BlurGodraysH")
        self.target_blur_h.size = "50%"
        self.target_blur_h.add_color_attachment(bits=(16, 0, 0, 0))
        self.target_blur_h.prepare_buffer()
        self.target_blur_h.set_shader_input("direction", LVecBase2i(0, 1))
        self.target_blur_h.set_shader_input("SourceTex", self.target_blur_v.color_tex)

        self.target_resolve = self.create_target("ResolveGodrays")
        self.target_resolve.add_color_attachment(bits=(16, 0, 0, 0))
        self.target_resolve.prepare_buffer()
        self.target_resolve.set_shader_input("SourceTex", self.target_blur_h.color_tex)

        self.target_merge = self.create_target("MergeGodrays")
        self.target_merge.add_color_attachment(bits=16)
        self.target_merge.prepare_buffer()

        self.target_merge.set_shader_input("GodrayTex", self.target_resolve.color_tex)

    def reload_shaders(self):
        self.target.shader = self.load_plugin_shader("compute_godrays.vert.glsl", "compute_godrays.frag.glsl")
        self.target_merge.shader = self.load_plugin_shader("merge_godrays.frag.glsl")
        self.target_mask.shader = self.load_plugin_shader("mask_sun.frag.glsl")
        self.target_resolve.shader = self.load_plugin_shader("resolve_godrays.frag.glsl")

        blur_shader = self.load_plugin_shader("blur_godrays.frag.glsl")
        self.target_blur_v.shader = blur_shader
        self.target_blur_h.shader = blur_shader

