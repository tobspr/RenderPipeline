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

from rpcore.render_stage import RenderStage


class ComputeLowPrecisionNormalsStage(RenderStage):

    """ This stage computes normals and low-precision depth from the depth buffer """

    required_pipes = ["GBuffer"]

    @property
    def produced_pipes(self):
        return {
            "LowPrecisionNormals": self.target.color_tex,
            "LowPrecisionHalfresNormals": self.target_half.color_tex
        }

    def create(self):
        self.target = self.create_target("ComputeLowPrecisionNormals")
        self.target.add_color_attachment(bits=(8, 8, 0, 0))
        self.target.prepare_buffer()

        self.target_half = self.create_target("DownscaleNormalsToHalf")
        self.target_half.add_color_attachment(bits=(8, 8, 0, 0))
        self.target_half.size = "50%"
        self.target_half.prepare_buffer()
        self.target_half.set_shader_input("SourceTex", self.target.color_tex)

    def reload_shaders(self):
        self.target.shader = self.load_shader("compute_low_precision_normals.frag.glsl")
        self.target_half.shader = self.load_shader("downscale_normals.frag.glsl")
