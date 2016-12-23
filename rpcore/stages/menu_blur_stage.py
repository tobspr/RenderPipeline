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

from panda3d.core import LVecBase2i, PTAFloat

from rpcore.globals import Globals
from rpcore.render_stage import RenderStage


class MenuBlurStage(RenderStage):

    """ This stage blurs the screen when a menu is active """

    required_inputs = []
    required_pipes = ["ShadedScene"]
    enable_during_menu = True

    @property
    def produced_pipes(self):
        return {
            "ShadedScene": self.target_combine.color_tex
        }

    def __init__(self, *args):
        RenderStage.__init__(self, *args)
        self.pta_blur_scale = PTAFloat.empty_array(1)
        self.blur_scale_velocity = 0
        self.blur_enabled = False
        self.stale_size = False

    def create(self):
        self.target_cache_scene = self.create_target("MenuCacheScene")
        self.target_cache_scene.size = Globals.resolution.x, Globals.resolution.y
        self.target_cache_scene.add_color_attachment(bits=8)
        self.target_cache_scene.prepare_buffer()

        self.blur_targets = []
        for i in range(8):
            target_blur = self.create_target("MenuBlur-" + str(i))
            target_blur.add_color_attachment(bits=8)
            target_blur.prepare_buffer()
            target_blur.set_shader_input("direction", LVecBase2i(i % 2, (i + 1) % 2))
            target_blur.set_shader_input("blurScale", self.pta_blur_scale)

            if i != 0:
                target_blur.set_shader_input(
                    "SourceTex", self.blur_targets[-1].color_tex, override=True)
            else:
                target_blur.set_shader_input(
                    "SourceTex", self.target_cache_scene.color_tex)
            self.blur_targets.append(target_blur)

        self.target_combine = self.create_target("ApplyMenuBlur")
        self.target_combine.add_color_attachment(bits=8)
        self.target_combine.prepare_buffer()
        self.target_combine.set_shader_input("BlurTex", self.blur_targets[-1].color_tex)
        self.disable_blur()

    def enable_blur(self):
        self.target_combine.set_shader_input("useBlur", True)
        for target in self.blur_targets:
            target.active = True
        self.pta_blur_scale[0] = 0.0
        self.blur_scale_velocity = 4.0
        self.target_cache_scene.active = False
        self.blur_enabled = True

    def disable_blur(self):
        # XXX: Because all targets are disabled instantly, the blur does not fade
        # out. Need to first fade out, then disable targets
        self.target_combine.set_shader_input("useBlur", False)
        for target in self.blur_targets:
            target.active = False
        self.pta_blur_scale[0] = 1.0
        self.blur_scale_velocity = -1.5
        self.target_cache_scene.active = True
        self.blur_enabled = False

    def set_dimensions(self):
        self.stale_size = True

    def update(self):
        dt = self.blur_scale_velocity * Globals.clock.get_dt()
        self.pta_blur_scale[0] = max(0.0, min(1.0, self.pta_blur_scale[0] + dt))
        # self.blur_scale_velocity *= max(0.0, 1.0 - Globals.clock.get_dt())
        self.blur_scale_velocity *= 0.94

        if self.stale_size and not self.blur_enabled:
            # During the blur, the window was resized, but to preserve the scene
            # data, we only resize or cache target *after* the blur is no longer
            # visible
            self.debug("Resize blur target to", Globals.resolution)
            self.target_cache_scene.size = Globals.resolution.x, Globals.resolution.y
            self.stale_size = False

    def reload_shaders(self):
        self.target_cache_scene.shader = self.load_shader("menu_blur_cache_scene.frag.glsl")
        blur_shader = self.load_shader("menu_blur.frag.glsl")
        for target in self.blur_targets:
            target.shader = blur_shader
        self.target_combine.shader = self.load_shader("apply_menu_blur.frag.glsl")
