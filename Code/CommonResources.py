
from panda3d.core import PTAVecBase3f, PTAMat4, Texture, TransformState, Mat4
from panda3d.core import CS_yup_right, CS_zup_right, PTAFloat, invert
from direct.stdpy.file import open

from .Util.DebugObject import DebugObject
from .Globals import Globals
from .BaseManager import BaseManager

from .Util.ShaderUBO import PTABasedUBO

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
        Globals.font = Globals.loader.loadFont("Data/Font/Roboto-Medium.ttf")
        Globals.font.set_pixels_per_unit(35)
        Globals.font.set_poly_margin(0.0)
        Globals.font.set_texture_margin(1)

    def _setup_inputs(self):
        """ Creates commonly used shader inputs such as the current mvp and
        registers them to the stage manager so they can be used for rendering """

        self._input_ubo = PTABasedUBO("MainSceneData")
        self._input_ubo.register_pta("camera_pos", "vec3")
        self._input_ubo.register_pta("view_proj_mat_no_jitter", "mat4")
        self._input_ubo.register_pta("last_view_proj_mat_no_jitter", "mat4")
        self._input_ubo.register_pta("view_mat_z_up", "mat4")
        self._input_ubo.register_pta("proj_mat", "mat4")
        self._input_ubo.register_pta("inv_proj_mat", "mat4")
        self._input_ubo.register_pta("frame_delta", "float")
        self._pipeline.get_stage_mgr().add_ubo(self._input_ubo)

        # Main camera and main render have to be regular inputs, since they are
        # used in the shaders by that name.
        self._pipeline.get_stage_mgr().add_input("mainCam", self._showbase.cam)
        self._pipeline.get_stage_mgr().add_input("mainRender", self._showbase.render)

    def write_config(self):
        """ Generates the shader configuration for the common inputs """
        content = self._input_ubo.generate_shader_code()
        try:
            # Try to write the temporary file
            with open("$$PipelineTemp/$$MainSceneData.inc.glsl", "w") as handle:
                handle.write(content)
        except IOError as msg:
            self.error("Failed to write common resources shader configuration!", msg)

    def _load_textures(self):
        """ Loads commonly used textures and makes them available via the
        stage manager """
        self._load_normal_quantization()
        self._load_environment_cubemap()
        self._load_precomputed_grain()
        self._load_prefilter_brdf()
        self._load_skydome()

    def _load_normal_quantization(self):
        """ Loads the normal quantization tex, used to compress normals to
        8 bit in the GBuffer, based on a method suggested by the cryengine. """
        quant_tex = Globals.loader.loadTexture(
            "Data/NormalQuantization/NormalQuantizationTex-#.png",
            readMipmaps=True)
        # quant_tex = Globals.loader.loadTexture(
            # "Data/NormalQuantization/Reference.png")
        quant_tex.set_minfilter(Texture.FT_linear_mipmap_linear)
        quant_tex.set_magfilter(Texture.FT_linear)
        quant_tex.set_wrap_u(Texture.WM_mirror)
        quant_tex.set_wrap_v(Texture.WM_mirror)
        quant_tex.set_anisotropic_degree(0)
        quant_tex.set_format(Texture.F_r16)
        self._showbase.render.set_shader_input("NormalQuantizationTex", quant_tex)

    def _load_environment_cubemap(self):
        """ Loads the default cubemap used for the environment, which is used
        when no other environment data is available """
        envmap = Globals.loader.loadCubeMap(
            "Data/DefaultCubemap/Filtered/#-#.png", readMipmaps=True)
        envmap.set_minfilter(Texture.FT_linear_mipmap_linear)
        envmap.set_magfilter(Texture.FT_linear)
        envmap.set_wrap_u(Texture.WM_repeat)
        envmap.set_wrap_v(Texture.WM_repeat)
        envmap.set_wrap_w(Texture.WM_repeat)
        self._pipeline.get_stage_mgr().add_input("DefaultEnvmap", envmap)

    def _load_prefilter_brdf(self):
        """ Loads the prefiltered brdf """
        brdf_tex = Globals.loader.loadTexture(
            "Data/EnvironmentBRDF/PrefilteredEnvBRDF.png")
        brdf_tex.set_minfilter(Texture.FT_linear)
        brdf_tex.set_magfilter(Texture.FT_linear)
        brdf_tex.set_wrap_u(Texture.WM_clamp)
        brdf_tex.set_wrap_v(Texture.WM_clamp)
        brdf_tex.set_anisotropic_degree(0)
        brdf_tex.set_format(Texture.F_rgba16)
        self._pipeline.get_stage_mgr().add_input("PrefilteredBRDF", brdf_tex)

    def _load_precomputed_grain(self):
        grain_tex = Globals.loader.loadTexture(
            "Data/PrecomputedGrain/grain.png")
        grain_tex.set_minfilter(Texture.FT_linear)
        grain_tex.set_magfilter(Texture.FT_linear)
        grain_tex.set_wrap_u(Texture.WM_repeat)
        grain_tex.set_wrap_v(Texture.WM_repeat)
        grain_tex.set_anisotropic_degree(0)
        self._pipeline.get_stage_mgr().add_input("PrecomputedGrain", grain_tex)  

    def _load_skydome(self):
        """ Loads the skydome """
        skydome = Globals.loader.loadTexture("Data/BuiltinModels/Skybox/Skybox2.jpg")
        skydome.set_wrap_u(Texture.WM_clamp)
        skydome.set_wrap_v(Texture.WM_clamp)
        self._pipeline.get_stage_mgr().add_input("DefaultSkydome", skydome)

    def load_default_skybox(self):
        skybox = Globals.loader.loadModel("Data/BuiltinModels/Skybox/Skybox.bam")
        return skybox

    def do_update(self):
        """ Updates the commonly used resources, mostly the shader inputs """
        update = self._input_ubo.update_input

        # Get the current transform matrix of the camera
        view_mat = Globals.render.get_transform(self._showbase.cam).get_mat()

        # Compute the view matrix, but with a z-up coordinate system 
        update("view_mat_z_up", view_mat * Mat4.convert_mat(CS_zup_right, CS_yup_right))
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
