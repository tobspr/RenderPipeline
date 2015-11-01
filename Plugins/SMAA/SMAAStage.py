from __future__ import division

from .. import *

from panda3d.core import Texture


class SMAAStage(RenderStage):

    """ This stage does the actual SMAA """

    required_pipes = ["ShadedScene", "GBufferDepth", "ColorCorrectedScene"]
    required_inputs = ["mainCam", "mainRender", "cameraPosition"]

    def __init__(self, pipeline):
        RenderStage.__init__(self, "SMAAStage", pipeline)
        self._area_tex = None
        self._search_tex = None

    def set_area_tex(self, tex):
        self._area_tex = tex

    def set_search_tex(self, tex):
        self._search_tex = tex

    def get_produced_pipes(self):
        return {"ColorCorrectedScene": self._neighbor_target['color']}

    def create(self):
        self._edge_target = self._create_target("SMAAEdges")
        self._edge_target.add_color_texture()
        self._edge_target.set_color_bits(16)
        self._edge_target.prepare_offscreen_buffer()
        self._edge_target.set_clear_color()

        self._blend_target = self._create_target("SMAABlendWeights")
        self._blend_target.add_color_texture()
        self._blend_target.set_color_bits(16)
        self._blend_target.prepare_offscreen_buffer()
        self._blend_target.set_clear_color()

        self._blend_target.set_shader_input("EdgeTex", self._edge_target["color"])
        self._blend_target.set_shader_input("AreaTex", self._area_tex)
        self._blend_target.set_shader_input("SearchTex", self._search_tex)

        self._neighbor_target = self._create_target("SMAANeighbor")
        self._neighbor_target.add_color_texture()
        self._neighbor_target.set_color_bits(16)
        self._neighbor_target.prepare_offscreen_buffer()
        self._neighbor_target.set_clear_color()

        self._neighbor_target.set_shader_input("BlendTex", self._blend_target["color"])

    def set_shaders(self):
        self._edge_target.set_shader(self.load_plugin_shader("EdgeDetection.frag.glsl"))
        self._blend_target.set_shader(self.load_plugin_shader("BlendingWeights.frag.glsl"))
        self._neighbor_target.set_shader(self.load_plugin_shader("NeighborhoodBlending.frag.glsl"))

    def resize(self):
        RenderStage.resize(self)
        self.debug("Resizing pass")

    def cleanup(self):
        RenderStage.cleanup(self)
        self.debug("Cleanup pass")
