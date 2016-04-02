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

from panda3d.core import SamplerState, Vec4

from rpcore.globals import Globals
from rpcore.image import Image
from rpcore.render_stage import RenderStage
from rpcore.stages.ambient_stage import AmbientStage

class SSRStage(RenderStage):

    """ This stage does the SSR pass """

    required_inputs = []
    required_pipes = ["ShadedScene", "CombinedVelocity", "GBuffer",
                      "DownscaledDepth", "PreviousFrame::PostAmbientScene",
                      "PreviousFrame::SSRSpecular", "PreviousFrame::SceneDepth"]

    @property
    def produced_pipes(self):
        return { "SSRSpecular": self.target_post_blur.color_tex }

    def create(self):
        x_size, y_size = Globals.resolution.x, Globals.resolution.y

        self.target = self.create_target("ComputeSSR")
        self.target.size = -2
        self.target.add_color_attachment(bits=16)
        self.target.prepare_buffer()

        self.target.color_tex.set_minfilter(SamplerState.FT_nearest)
        self.target.color_tex.set_magfilter(SamplerState.FT_nearest)

        self.target_velocity = self.create_target("ReflectionVelocity")
        self.target_velocity.add_color_attachment(bits=(16, 16, 0, 0))
        self.target_velocity.prepare_buffer()
        self.target_velocity.set_shader_input("TraceResult", self.target.color_tex)

        self.mipchain = Image.create_2d("SSRMipchain", x_size, y_size, "RGBA16")
        self.mipchain.set_minfilter(SamplerState.FT_linear_mipmap_linear)
        self.mipchain.set_wrap_u(SamplerState.WM_clamp)
        self.mipchain.set_wrap_v(SamplerState.WM_clamp)
        self.mipchain.set_clear_color(Vec4(0))
        self.mipchain.clear_image()

        self.target_copy_lighting = self.create_target("CopyLighting")
        self.target_copy_lighting.prepare_buffer()
        self.target_copy_lighting.set_shader_input("DestTex", self.mipchain, False, True, -1, 0)

        self.blur_targets = []
        for i in range(min(7, self.mipchain.get_expected_num_mipmap_levels() - 1)):
            target_blur = self.create_target("BlurSSR-" + str(i))
            target_blur.size = - (2 ** i)
            target_blur.prepare_buffer()
            target_blur.set_shader_input("SourceTex", self.mipchain)
            target_blur.set_shader_input("sourceMip", i)
            target_blur.set_shader_input("DestTex", self.mipchain, False, True, -1, i + 1)
            self.blur_targets.append(target_blur)

        self.noise_reduce_targets = []
        curr_tex = self.target.color_tex
        for i in range(0):
            target_remove_noise = self.create_target("RemoveNoise")
            target_remove_noise.size = -2
            target_remove_noise.add_color_attachment(bits=16, alpha=True)
            target_remove_noise.prepare_buffer()
            target_remove_noise.set_shader_input("SourceTex", curr_tex)
            curr_tex = target_remove_noise.color_tex
            self.noise_reduce_targets.append(target_remove_noise)

        self.fill_hole_targets = []
        for i in range(0):
            fill_target = self.create_target("FillHoles-" + str(i))
            fill_target.size = -2
            fill_target.add_color_attachment(bits=16, alpha=True)
            fill_target.prepare_buffer()
            fill_target.set_shader_input("SourceTex", curr_tex)
            curr_tex = fill_target.color_tex
            self.fill_hole_targets.append(fill_target)

        self.target_upscale = self.create_target("UpscaleSSR")
        self.target_upscale.add_color_attachment(bits=16, alpha=True)
        self.target_upscale.prepare_buffer()
        self.target_upscale.set_shader_input("SourceTex", curr_tex)
        self.target_upscale.set_shader_input("MipChain", self.mipchain)

        self.target_resolve = self.create_target("ResolveSSR")
        self.target_resolve.add_color_attachment(bits=16, alpha=True)
        self.target_resolve.prepare_buffer()
        self.target_resolve.set_shader_input("CurrentTex", self.target_upscale.color_tex)
        self.target_resolve.set_shader_input("VelocityTex", self.target_velocity.color_tex)

        self.target_post_blur = self.create_target("SSRPostBlur")
        self.target_post_blur.add_color_attachment(bits=16, alpha=True)
        self.target_post_blur.prepare_buffer()
        self.target_post_blur.set_shader_input("CurrentTex", self.target_resolve.color_tex)

        AmbientStage.required_pipes.append("SSRSpecular")

    def reload_shaders(self):
        self.target.shader = self.load_plugin_shader("ssr_trace.frag.glsl")
        self.target_velocity.shader = self.load_plugin_shader("reflection_velocity.frag.glsl")
        self.target_copy_lighting.shader = self.load_plugin_shader("copy_lighting.frag.glsl")
        self.target_post_blur.shader = self.load_plugin_shader("ssr_post_blur.frag.glsl")
        self.target_upscale.shader = self.load_plugin_shader("upscale_bilateral_brdf.frag.glsl")
        self.target_resolve.shader = self.load_plugin_shader("resolve_ssr.frag.glsl")
        blur_shader = self.load_plugin_shader("ssr_blur.frag.glsl")
        for target in self.blur_targets:
            target.shader = blur_shader
        remove_noise_shader = self.load_plugin_shader("remove_noise.frag.glsl")
        for target in self.noise_reduce_targets:
            target.shader = remove_noise_shader
        fill_holes_shader = self.load_plugin_shader("fill_holes.frag.glsl")
        for target in self.fill_hole_targets:
            target.shader = fill_holes_shader
