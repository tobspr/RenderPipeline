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

from panda3d.core import Vec4, Vec3, Texture, TexturePool

from rpcore.loader import RPLoader
from rpcore.render_stage import RenderStage
from rpcore.globals import Globals

class ReferenceStage(RenderStage):

    """ This stage is used for the reference mode, to reduce noise"""

    REFERENCE_MODES = ["PIPELINE", "MITSUBA", "DIFFERENCE"]
    CURRENT_MODE = "PIPELINE"

    required_pipes = ["ShadedScene", "PreviousFrame::PostReferenceStage[RGBA16]"]

    # FIXME: Refactor this code, and move code out of the debugger calling this.

    @classmethod
    def switch_to_mode(cls, mode):
        cls.CURRENT_MODE = mode

    def __init__(self, *args):
        RenderStage.__init__(self, *args)
        self.current_mode = "PIPELINE"
        self.current_tex = Texture("")

    @property
    def produced_pipes(self):
        return {
            "ShadedScene": self.target.color_tex,
            "PostReferenceStage": self.target.color_tex
        }

    def create(self):
        self.last_cam_pos = Vec3(0)
        self.last_cam_hpr = Vec3(0)

        self.target = self.create_target("ReferenceOverlay")
        # NOTICE: 16bit is really required for proper fading between images,
        # otherwise pixels can "stay" because for example 32.99 * 0.99 = 32.5 = 32 -> Pixel stays
        self.target.add_color_attachment(bits=16)
        self.target.prepare_buffer()
        self.target.set_clear_color(Vec4(1, 0, 0, 0))
        self.target.set_shader_input("cameraMoved", False)

        self.target.set_shader_input("ReferenceTex", self.current_tex)
        self.target.set_shader_input("displayReference", False)
        self.target.set_shader_input("displayDifference", False)


    def update(self):
        # Invalidate on camera movement / rotation change
        curr_pos = Globals.base.cam.get_pos(Globals.base.render)
        curr_hpr = Globals.base.cam.get_hpr(Globals.base.render)
        dist = (curr_pos - self.last_cam_pos).length()
        dist += (curr_hpr - self.last_cam_hpr).length()
        self.last_cam_pos = curr_pos
        self.last_cam_hpr = curr_hpr
        self.target.set_shader_input("cameraMoved", dist > 0.01)

        if self.current_mode != ReferenceStage.CURRENT_MODE:
            self.debug("Switching from", self.current_mode, "to", ReferenceStage.CURRENT_MODE)
            self.current_mode = ReferenceStage.CURRENT_MODE

            if self.current_mode == "PIPELINE":
                self.target.set_shader_input("displayReference", False)
                self.target.set_shader_input("displayDifference", False)

            elif self.current_mode == "MITSUBA":
                self.target.set_shader_input("displayReference", True)
                self.target.set_shader_input("displayDifference", False)

                TexturePool.release_texture(self.current_tex)
                self.current_tex = None

                # Load scene image
                try:
                    self.current_tex = RPLoader.load_texture("exported/scene.png")
                except Exception:  # pylint: disable=broad-except
                    self.warn("No reference render found")
                    self.current_tex = Texture("")
                    self.target.set_shader_input("ReferenceTex", self.current_tex)
                    self.target.set_shader_input("displayReference", False)
                    self.target.set_shader_input("displayDifference", False)

            elif self.current_mode == "DIFFERENCE":
                self.target.set_shader_input("displayReference", True)
                self.target.set_shader_input("displayDifference", True)

            self.target.set_shader_input("ReferenceTex", self.current_tex)

    def reload_shaders(self):
        self.target.shader = self.load_shader("reference_overlay.frag.glsl")
