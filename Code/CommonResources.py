
from panda3d.core import PTAVecBase3f, PTAMat4, Texture, TransformState, Mat4
from panda3d.core import CSYupRight, CSZupRight

from .Util.DebugObject import DebugObject
from .Globals import Globals


class CommonResources(DebugObject):

    """ This class manages the loading and binding of commonly used resources,
    such as textures, models, but also shader inputs """

    def __init__(self, pipeline):
        DebugObject.__init__(self)
        self._pipeline = pipeline
        self._showbase = Globals.base

    def load(self):
        """ Loads and binds the commonly used resources """
        self._load_fonts()
        self._load_textures()
        self._setup_inputs()

    def _load_fonts(self):
        """ Loads the default font used for rendering and assigns it to 
        Globals.font for further usage """
        # Globals.font = Globals.loader.loadFont("Data/Font/Roboto-Light.ttf")
        # Globals.font = Globals.loader.loadFont("Data/Font/SourceSansPro-Bold.otf")
        Globals.font = Globals.loader.loadFont("Data/Font/DebugFont.ttf")
        Globals.font.set_pixels_per_unit(25)
        Globals.font.set_poly_margin(0.0)
        Globals.font.set_texture_margin(1)

    def _setup_inputs(self):
        """ Creates commonly used shader inputs such as the current mvp and
        registers them to the stage manager so they can be used for rendering """
        self._pta_camera_pos = PTAVecBase3f.empty_array(1)
        self._pta_current_view_proj_mat = PTAMat4.empty_array(1)
        self._pta_view_mat_zup = PTAMat4.empty_array(1)

        stage_mgr = self._pipeline.get_stage_mgr()
        stage_mgr.add_input("mainCam", self._showbase.cam)
        stage_mgr.add_input("mainRender", self._showbase.render)
        stage_mgr.add_input("cameraPosition", self._pta_camera_pos)
        stage_mgr.add_input("currentViewProjMat", self._pta_current_view_proj_mat)
        stage_mgr.add_input("currentViewMatZup", self._pta_view_mat_zup)

        # Create a converter matrix to transform coordinates from Yup to Zup
        self._coordinate_converter = TransformState.make_mat(
            Mat4.convert_mat(CSYupRight, CSZupRight))

    def _load_textures(self):
        """ Loads commonly used textures and makes them available via the
        stage manager """
        self._load_normal_quantization()
        self._load_environment_cubemap()
        self._load_skydome()

    def _load_normal_quantization(self):
        """ Loads the normal quantization tex, used to compress normals to
        8 bit in the GBuffer, based on a method suggested by the cryengine. """
        quant_tex = Globals.loader.loadTexture(
            "Data/NormalQuantization/NormalQuantizationTex-#.png",
            readMipmaps=True)
        quant_tex.set_minfilter(Texture.FT_linear_mipmap_linear)
        quant_tex.set_magfilter(Texture.FT_linear)
        quant_tex.set_wrap_u(Texture.WM_repeat)
        quant_tex.set_wrap_v(Texture.WM_repeat)
        quant_tex.set_format(Texture.F_rgba16)
        self._showbase.render.set_shader_input("NormalQuantizationTex", quant_tex)

    def _load_environment_cubemap(self):
        """ Loads the default cubemap used for the environment, which is used
        when no other environment data is available """
        self.debug("Loading environment cubemap")
        envmap = Globals.loader.loadCubeMap(
            "Data/DefaultCubemap/Filtered/#-#.png", readMipmaps=True)
        envmap.set_minfilter(Texture.FT_linear_mipmap_linear)
        envmap.set_magfilter(Texture.FT_linear)
        envmap.set_wrap_u(Texture.WM_repeat)
        envmap.set_wrap_v(Texture.WM_repeat)
        envmap.set_wrap_w(Texture.WM_repeat)
        self._pipeline.get_stage_mgr().add_input("DefaultEnvmap", envmap)

    def _load_skydome(self):
        """ Loads the skydome """
        self.debug("Loading skydome ..")
        skydome = Globals.loader.loadTexture("Data/BuiltinModels/Skybox/Skybox2.jpg")
        skydome.set_wrap_u(Texture.WM_clamp)
        skydome.set_wrap_v(Texture.WM_clamp)
        self._pipeline.get_stage_mgr().add_input("DefaultSkydome", skydome)

    def load_default_skybox(self):
        skybox = Globals.loader.loadModel("Data/BuiltinModels/Skybox/Skybox.egg.bam")
        return skybox

    def update(self):
        """ Updates the commonly used resources, mostly the shader inputs """
        view_transform = self._showbase.render.get_transform(self._showbase.cam)
        self._pta_view_mat_zup[0] = (
            self._coordinate_converter.invert_compose(view_transform).get_mat())
        self._pta_camera_pos[0] = self._showbase.camera.get_pos(render)
        self._pta_current_view_proj_mat[0] = view_transform.get_mat() *\
            self._showbase.camLens.get_projection_mat()

