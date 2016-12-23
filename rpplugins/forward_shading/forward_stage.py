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

from panda3d.core import Camera, LVecBase2i

from rpcore.image import Image
from rpcore.globals import Globals
from rpcore.render_stage import RenderStage


class ForwardStage(RenderStage):

    """ Forward shading stage, which first renders all forward objects,
    and then merges them with the scene """

    required_inputs = ["AllLightsData", "IESDatasetTex", "ShadowSourceData",
                       "DebugFontAtlas", "LTCAmpTex", "LTCMatTex", "DefaultEnvmapSpec",
                       "DefaultEnvmapDiff"]
    required_pipes = ["GBuffer", "CellIndices", "PerCellLights", "ShadowAtlas",
                      "ShadowAtlasPCF", "CombinedVelocity", "PerCellLightsCounts",
                      "ShadedScene", "SceneDepth"]

    @property
    def produced_pipes(self):
        return {"ShadedScene": self.target_merge.color_tex}

    def create(self):
        self.forward_cam = Camera("ForwardShadingCam")
        self.forward_cam.set_lens(Globals.base.camLens)
        self.forward_cam_np = Globals.base.camera.attach_new_node(self.forward_cam)

        # Stores the total amount of fragments allocated
        self.fragment_counter = Image.create_counter("ForwardFragmentCounter")

        # Stores the per fragment data, in the format (rgb-color, alpha)
        self.fragment_data = Image.create_buffer("ForwardFragmentData", 0, "RGBA16")

        # Stores the per fragment depth
        self.fragment_depth = Image.create_buffer("ForwardFragmentDepth", 0, "R32")  # XXX: Examine R16

        # Stores the pointer to the next fragment, or null if none exists
        self.fragment_next = Image.create_buffer("ForwardFragmentNext", 0, "R32UI")

        # For each pixel, stores the start of the linked list, or null if its empty
        self.linked_list_head = Image.create_2d("ForwardLinkedListHead", 0, 0, "R32UI")

        self.target = self.create_target("ForwardShading")
        self.target.prepare_render(self.forward_cam_np)
        self.target.set_clear_color(0, 0, 0, 0)

        self._pipeline.tag_mgr.register_camera("forward", self.forward_cam)

        self.target_blur_x = self.create_target("ForwardBlurX")
        self.target_blur_x.add_color_attachment(bits=16)
        self.target_blur_x.prepare_buffer()
        self.target_blur_x.set_shader_input("direction", LVecBase2i(1, 0))

        self.target_blur_y = self.create_target("ForwardBlurY")
        self.target_blur_y.add_color_attachment(bits=16)
        self.target_blur_y.prepare_buffer()
        self.target_blur_y.set_shader_input("direction", LVecBase2i(0, 1))

        self.target_blur_y.set_shader_input("ShadedScene", self.target_blur_x.color_tex, override=True)

        self.target_merge = self.create_target("MergeForwardWithDeferred")
        self.target_merge.add_color_attachment(bits=16)
        self.target_merge.prepare_buffer()
        self.target_merge.set_shader_input("BlurredShadedScene", self.target_blur_y.color_tex)

        self.set_shader_input("ForwardFragmentCounter", self.fragment_counter)
        self.set_shader_input("ForwardFragmentData", self.fragment_data)
        self.set_shader_input("ForwardFragmentDepth", self.fragment_depth)
        self.set_shader_input("ForwardFragmentNext", self.fragment_next)
        self.set_shader_input("ForwardLinkedListHead", self.linked_list_head)

    def set_dimensions(self):
        max_layers = 3  # XXX: Make configurable
        pixels = Globals.resolution.x * Globals.resolution.y
        max_fragments = pixels * max_layers
        self.debug("Max fragments =", max_fragments)
        self.fragment_data.resize(max_fragments)
        self.fragment_next.resize(max_fragments)
        self.fragment_depth.resize(max_fragments)
        self.linked_list_head.resize(Globals.resolution.x, Globals.resolution.y)

    def update(self):
        self.fragment_counter.clear_image()

        # If this clear ever gets too slow, we can store even indexes in the one frame,
        # and uneven in the next. Then we can just check if the index matches,
        # instead of having to clear the whole texture
        self.linked_list_head.clear_image()

    def set_shader_input(self, *args):
        Globals.base.render.set_shader_input(*args)
        RenderStage.set_shader_input(self, *args)

    def reload_shaders(self):
        self.target_merge.shader = self.load_plugin_shader("merge_with_deferred.frag.glsl")
        blur_shader = self.load_plugin_shader("pre_blur_forward.frag.glsl")
        self.target_blur_x.shader = blur_shader
        self.target_blur_y.shader = blur_shader
