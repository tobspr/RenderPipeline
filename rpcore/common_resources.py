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

import random

from panda3d.core import CS_yup_right, CS_zup_right, invert, Vec3, Texture, Mat4
from panda3d.core import SamplerState, PNMImage
from direct.stdpy.file import open

from rpcore.image import Image
from rpcore.globals import Globals
from rpcore.base_manager import BaseManager

from rpcore.util.shader_ubo import ShaderUBO

class CommonResources(BaseManager):

    """ This class manages the loading and binding of commonly used resources,
    such as textures, models, but also shader inputs """

    def __init__(self, pipeline):
        BaseManager.__init__(self)
        self._pipeline = pipeline
        self._showbase = Globals.base
        self._ptas = {}
        self._load_fonts()
        self._load_textures()
        self._setup_inputs()

    def _load_fonts(self):
        """ Loads the default font used for rendering and assigns it to
        Globals.font for further usage """
        Globals.font = Globals.loader.loadFont("data/font/roboto-medium.ttf")
        Globals.font.set_pixels_per_unit(35)
        Globals.font.set_poly_margin(0.0)
        Globals.font.set_texture_margin(1)

    def _setup_inputs(self):
        """ Creates commonly used shader inputs such as the current mvp and
        registers them to the stage manager so they can be used for rendering """

        self._input_ubo = ShaderUBO("MainSceneData")
        self._input_ubo.register_pta("camera_pos", "vec3")
        self._input_ubo.register_pta("view_proj_mat_no_jitter", "mat4")
        self._input_ubo.register_pta("last_view_proj_mat_no_jitter", "mat4")
        self._input_ubo.register_pta("view_mat_z_up", "mat4")
        self._input_ubo.register_pta("proj_mat", "mat4")
        self._input_ubo.register_pta("inv_proj_mat", "mat4")
        self._input_ubo.register_pta("view_mat_billboard", "mat4")
        self._input_ubo.register_pta("frame_delta", "float")
        self._input_ubo.register_pta("frame_time", "float")
        self._pipeline.stage_mgr.add_ubo(self._input_ubo)

        # Main camera and main render have to be regular inputs, since they are
        # used in the shaders by that name.
        self._pipeline.stage_mgr.add_input("mainCam", self._showbase.cam)
        self._pipeline.stage_mgr.add_input("mainRender", self._showbase.render)

    def write_config(self):
        """ Generates the shader configuration for the common inputs """
        content = self._input_ubo.generate_shader_code()
        try:
            # Try to write the temporary file
            with open("$$pipeline_temp/$$main_scene_data.inc.glsl", "w") as handle:
                handle.write(content)
        except IOError as msg:
            self.error("Failed to write common resources shader configuration!", msg)

    def _load_textures(self):
        """ Loads commonly used textures and makes them available via the
        stage manager """
        self._load_environment_cubemap()
        self._load_precomputed_grain()
        self._load_prefilter_brdf()
        self._load_skydome()
        self._load_noise_tex()

    def _load_environment_cubemap(self):
        """ Loads the default cubemap used for the environment, which is used
        when no other environment data is available """
        envmap = Globals.loader.loadCubeMap(
            "data/default_cubemap/filtered/#-#.png", readMipmaps=True)
        envmap.set_minfilter(SamplerState.FT_linear_mipmap_linear)
        envmap.set_format(Texture.F_rgba16)
        envmap.set_magfilter(SamplerState.FT_linear)
        envmap.set_wrap_u(SamplerState.WM_repeat)
        envmap.set_wrap_v(SamplerState.WM_repeat)
        envmap.set_wrap_w(SamplerState.WM_repeat)
        self._pipeline.stage_mgr.add_input("DefaultEnvmap", envmap)

    def _load_prefilter_brdf(self):
        """ Loads the prefiltered brdf """
        brdf_tex = Globals.loader.loadTexture(
            "data/environment_brdf/prefiltered_environment_brdf.png")
        brdf_tex.set_minfilter(SamplerState.FT_linear)
        brdf_tex.set_magfilter(SamplerState.FT_linear)
        brdf_tex.set_wrap_u(SamplerState.WM_clamp)
        brdf_tex.set_wrap_v(SamplerState.WM_clamp)
        brdf_tex.set_anisotropic_degree(0)
        brdf_tex.set_format(Texture.F_rgba16)
        self._pipeline.stage_mgr.add_input("PrefilteredBRDF", brdf_tex)

    def _load_precomputed_grain(self):
        grain_tex = Globals.loader.loadTexture(
            "data/film_grain/grain.png")
        grain_tex.set_minfilter(SamplerState.FT_linear)
        grain_tex.set_magfilter(SamplerState.FT_linear)
        grain_tex.set_wrap_u(SamplerState.WM_repeat)
        grain_tex.set_wrap_v(SamplerState.WM_repeat)
        grain_tex.set_anisotropic_degree(0)
        self._pipeline.stage_mgr.add_input("PrecomputedGrain", grain_tex)

    def _load_skydome(self):
        """ Loads the skydome """
        skydome = Globals.loader.loadTexture("data/builtin_models/skybox/skybox.jpg")
        skydome.set_wrap_u(SamplerState.WM_clamp)
        skydome.set_wrap_v(SamplerState.WM_clamp)
        self._pipeline.stage_mgr.add_input("DefaultSkydome", skydome)

    def _load_noise_tex(self):
        """ Loads the default 4x4 noise tex """
        random.seed(42)
        img = PNMImage(4, 4, 3)
        for x in range(16):
            img.set_xel(x % 4, x // 4, random.random(), random.random(), random.random())
        tex = Image("Noise4x4")
        tex.load(img)
        self._pipeline.stage_mgr.add_input("Noise4x4", tex)

    def load_default_skybox(self):
        skybox = Globals.loader.loadModel("data/builtin_models/skybox/skybox.bam")
        return skybox

    def do_update(self):
        """ Updates the commonly used resources, mostly the shader inputs """
        update = self._input_ubo.update_input

        # Get the current transform matrix of the camera
        view_mat = Globals.render.get_transform(self._showbase.cam).get_mat()

        # Compute the view matrix, but with a z-up coordinate system
        update("view_mat_z_up", view_mat * Mat4.convert_mat(CS_zup_right, CS_yup_right))

        # Compute the view matrix without the camera rotation
        view_mat_billboard = Mat4(view_mat)
        view_mat_billboard.set_row(0, Vec3(1, 0, 0))
        view_mat_billboard.set_row(1, Vec3(0, 1, 0))
        view_mat_billboard.set_row(2, Vec3(0, 0, 1))
        update("view_mat_billboard", view_mat_billboard)

        update("camera_pos", self._showbase.camera.get_pos(Globals.render))
        update("last_view_proj_mat_no_jitter", self._input_ubo.get_input("view_proj_mat_no_jitter"))
        proj_mat = Mat4(self._showbase.camLens.get_projection_mat())

        # Set the projection matrix as an input, but convert it to the correct
        # coordinate system before.
        proj_mat_zup = Mat4.convert_mat(CS_yup_right, CS_zup_right) * proj_mat
        update("proj_mat", proj_mat_zup)

        # Set the inverse projection matrix
        update("inv_proj_mat", invert(proj_mat_zup))

        # Remove jitter and set the new view projection mat
        proj_mat.set_cell(1, 0, 0.0)
        proj_mat.set_cell(1, 1, 0.0)
        update("view_proj_mat_no_jitter", view_mat  * proj_mat)

        # Store the frame delta
        update("frame_delta", Globals.clock.get_dt())
        update("frame_time", Globals.clock.get_frame_time())
