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


class SMAAStage(RenderStage):

    """ This stage does the actual SMAA """

    required_inputs = []
    required_pipes = ["ShadedScene", "GBuffer"]
        
    def __init__(self, pipeline):
        RenderStage.__init__(self, pipeline)
        self.area_tex = None
        self.search_tex = None
    @property
    def produced_pipes(self):
        return {"ShadedScene": self.neighbor_target.color_tex}

    def create(self):
        # Pre-detect edges (predication)
        self.predicate_target = self.create_target("SMAApredicate")
        self.predicate_target.add_color_attachment(alpha=True)
        self.predicate_target.prepare_buffer()

        # Edge detection
        self.edge_target = self.create_target("EdgeDetection")
        self.edge_target.add_color_attachment(bits=(8, 8, 0, 0))
        self.edge_target.prepare_buffer()
        self.edge_target.set_clear_color(0, 0, 0, 0)
        self.edge_target.set_shader_input("PredicationTex", self.predicate_target.color_tex)

        # Weight blending
        self.blend_target = self.create_target("BlendWeights")
        self.blend_target.add_color_attachment(alpha=True)
        self.blend_target.prepare_buffer()

        self.blend_target.set_shader_input("EdgeTex", self.edge_target.color_tex)
        self.blend_target.set_shader_input("AreaTex", self.area_tex)
        self.blend_target.set_shader_input("SearchTex", self.search_tex)
        self.blend_target.set_shader_input("PredicationTex", self.predicate_target.color_tex)

        # Neighbor blending
        self.neighbor_target = self.create_target("NeighborBlending")
        self.neighbor_target.add_color_attachment()
        self.neighbor_target.prepare_buffer()
        self.neighbor_target.set_shader_input("BlendTex", self.blend_target.color_tex)

    def reload_shaders(self):
        self.edge_target.shader = self.load_plugin_shader("edge_detection.frag.glsl")
        self.blend_target.shader = self.load_plugin_shader("blending_weights.frag.glsl")
        self.neighbor_target.shader = self.load_plugin_shader("neighborhood_blending.frag.glsl")
        self.predicate_target.shader = self.load_plugin_shader("predication.frag.glsl")
        