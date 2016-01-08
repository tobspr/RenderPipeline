"""

RenderPipeline

Copyright (c) 2014-2015 tobspr <tobias.springer1@gmail.com>

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

from six.moves import range

from random import random, seed

from panda3d.core import LVecBase2i, PNMImage, Texture, Vec4

from .. import RenderStage

class AOStage(RenderStage):

    required_pipes = ["GBuffer"]
    required_inputs = []

    def __init__(self, pipeline):
        RenderStage.__init__(self, "AOStage", pipeline)

    def get_produced_pipes(self):
        return {"AmbientOcclusion": self._target_upscale['color']}

    def create(self):
        self._target = self._create_target("AO:Sample")
        self._target.add_color_texture(bits=8)
        self._target.prepare_offscreen_buffer()
        self._target.get_quad().set_instance_count(4)

        self._target_merge = self._create_target("AO:Merge")
        self._target_merge.set_half_resolution()
        self._target_merge.add_color_texture(bits=8)
        self._target_merge.prepare_offscreen_buffer()

        self._target_blur_v = self._create_target("AO:BlurV")
        self._target_blur_v.set_half_resolution()
        self._target_blur_v.add_color_texture(bits=8)
        self._target_blur_v.prepare_offscreen_buffer()

        self._target_blur_h = self._create_target("AO:BlurH")
        self._target_blur_h.set_half_resolution()
        self._target_blur_h.add_color_texture(bits=8)
        self._target_blur_h.prepare_offscreen_buffer()

        self._target_upscale = self._create_target("AO:Upscale")
        self._target_upscale.add_color_texture(bits=8)
        self._target_upscale.prepare_offscreen_buffer()

        self._target_upscale.set_shader_input("SourceTex", self._target_blur_h["color"])
        self._target_blur_v.set_shader_input("SourceTex", self._target_merge["color"])
        self._target_blur_h.set_shader_input("SourceTex", self._target_blur_v["color"])

        self._target_blur_v.set_shader_input("blur_direction", LVecBase2i(0, 1))
        self._target_blur_h.set_shader_input("blur_direction", LVecBase2i(1, 0))

        self._target_merge.set_shader_input("SourceTex", self._target["color"])

        self.create_noise_textures()

    def create_noise_textures(self):
        # Always generate the same random textures
        seed(42)
        img = PNMImage(4, 4, 3)
        for x in range(4):
            for y in range(4):
                img.set_xel(x, y, random(), random(), random())
        tex = Texture("Rand4x4")
        tex.load(img)
        self._target.set_shader_input("Noise4x4", tex)

    def set_shaders(self):
        self._target.set_shader(self.load_plugin_shader("AOSample.vert.glsl", "AOSample.frag.glsl"))
        self._target_upscale.set_shader(self.load_plugin_shader("AOUpscale.frag.glsl"))
        self._target_merge.set_shader(self.load_plugin_shader("AOMerge.frag.glsl"))

        blur_shader = self.load_plugin_shader("AOBlur.frag.glsl")
        self._target_blur_v.set_shader(blur_shader)
        self._target_blur_h.set_shader(blur_shader)

    def resize(self):
        RenderStage.resize(self)
        self.debug("Resizing pass")

    def cleanup(self):
        RenderStage.cleanup(self)
        self.debug("Cleanup pass")
