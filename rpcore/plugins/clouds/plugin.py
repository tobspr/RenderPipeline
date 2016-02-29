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

from panda3d.core import SamplerState

from rpcore.globals import Globals
from rpcore.pluginbase.base_plugin import BasePlugin

from .cloud_voxel_stage import CloudVoxelStage
from .apply_clouds_stage import ApplyCloudsStage

class Plugin(BasePlugin):

    name = "Volumetric Clouds"
    author = "tobspr <tobias.springer1@gmail.com>"
    description = ("This Plugin adds support or volumetric, raytraced clouds. "
                   "Right now this is pretty unoptimized and may consum a lot "
                   "of performance.")
    version = "alpha (!)"
    required_plugins = ("scattering",)

    def on_stage_setup(self):
        # self.generation_stage = self.create_stage(CloudVoxelStage)
        self.apply_stage = self.create_stage(ApplyCloudsStage)


    def on_pipeline_created(self):
        # Load noise texture

        tex_2d = Globals.loader.loadTexture(self.get_resource("tex_2d_1.png"))
        tex_3d_1 = load_sliced_3d_texture(self.get_resource("tex_3d_1.png", 128))
        tex_3d_2 = load_sliced_3d_texture(self.get_resource("tex_3d_2.png", 32))

        for tex in (tex_2d, tex_3d_1, tex_3d_2):
            tex.set_wrap_u(SamplerState.WM_repeat)
            tex.set_wrap_v(SamplerState.WM_repeat)
            tex.set_anisotropic_degree(0)
            tex.set_minfilter(SamplerState.FT_linear)
            tex.set_magfilter(SamplerState.FT_linear)

        self.apply_stage.set_shader_input("Noise2D", tex_2d)
        self.apply_stage.set_shader_input("Noise3D_128", tex_3d_1)
        self.apply_stage.set_shader_input("Noise3D_32", tex_3d_2)

