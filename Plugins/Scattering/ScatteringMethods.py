
from six.moves import range

from direct.stdpy.file import listdir, isfile, join
from panda3d.core import Texture, Shader

from .. import *

class ScatteringMethod(DebugObject):

    """ Base class for all scattering methods """

    def __init__(self, plugin_handle):
        DebugObject.__init__(self)
        self._handle = plugin_handle

    def load(self):
        """ Should load all required resources here """
        raise NotImplementedError()

    def compute(self):
        """ Should compute the model here if necessary """
        raise NotImplementedError()


class ScatteringMethodHosekWilkie(ScatteringMethod):

    """ Scattering as suggested by Hosek and Wilkie """

    def load(self):
        """ Loads the scattering method """
        lut_src = self._handle.get_resource("HosekWilkieScattering/ScatteringLUT.png")

        if not isfile(lut_src):
            self.error("Could not find precompiled LUT for the Hosek Wilkie "
                       "Scattering! Make sure you compiled the algorithm code!")
            return

        lut_tex = SliceLoader.load_3d_texture(lut_src, 512, 128, 100)
        lut_tex.set_wrap_u(Texture.WM_repeat)
        lut_tex.set_wrap_v(Texture.WM_clamp)
        lut_tex.set_wrap_w(Texture.WM_clamp)
        lut_tex.set_minfilter(Texture.FT_linear)
        lut_tex.set_magfilter(Texture.FT_linear)
        lut_tex.set_format(Texture.F_rgb16)

        self._handle._display_stage.set_shader_input("ScatteringLUT", lut_tex)

    def compute(self):
        """ Computes the scattering method, not required since we use a precomputed
        LUT """
        pass


class ScatteringMethodEricBruneton(ScatteringMethod):

    """ Precomputed atmospheric scattering by Eric Bruneton """

    def load(self):
        # Init sizes, those should match with the ones specified in common.glsl
        self._trans_w, self._trans_h = 256 * 4, 64 * 4
        self._sky_w, self._sky_h = 64 * 4, 16 * 4
        self._res_r, self._res_mu, self._res_mu_s, self._res_nu = 32, 128, 32, 8
        self._res_mu_s_nu = self._res_mu_s * self._res_nu

        self._create_shaders()
        self._create_textures()

    def _create_textures(self):
        """ Creates all textures required for the scattering """
        self._textures = {
            "transmittance": Image.create_2d(
                "scattering-transmittance", self._trans_w, self._trans_h,
                Texture.T_float, Texture.F_rgba32),

            "irradiance": Image.create_2d(
                "scattering-irradiance", self._sky_w, self._sky_h, Texture.T_float,
                Texture.F_rgba32),

            "inscatter": Image.create_3d(
                "scattering-inscatter", self._res_mu_s_nu, self._res_mu, self._res_r,
                Texture.T_float, Texture.F_rgba32),

            "delta_e": Image.create_2d(
                "scattering-dx-e", self._sky_w, self._sky_h, Texture.T_float,
                Texture.F_rgba32),

            "delta_sr": Image.create_3d(
                "scattering-dx-sr", self._res_mu_s_nu, self._res_mu, self._res_r,
                Texture.T_float, Texture.F_rgba32),

            "delta_sm": Image.create_3d(
                "scattering-dx-sm", self._res_mu_s_nu, self._res_mu, self._res_r,
                Texture.T_float, Texture.F_rgba32),

            "delta_j": Image.create_3d(
                "scattering-dx-j", self._res_mu_s_nu, self._res_mu, self._res_r,
                Texture.T_float, Texture.F_rgba32),
        }

        for img in self._textures.values():
            img.get_texture().set_minfilter(Texture.FT_linear)
            img.get_texture().set_magfilter(Texture.FT_linear)
            img.get_texture().set_wrap_u(Texture.WM_clamp)
            img.get_texture().set_wrap_v(Texture.WM_clamp)
            img.get_texture().set_wrap_w(Texture.WM_clamp)

    def _create_shaders(self):
        """ Creates all the shaders used for precomputing """
        self._shaders = {}
        resource_path = self._handle.get_shader_resource("eric_bruneton")
        for fname in listdir(resource_path):
            fpath = join(resource_path, fname)
            if isfile(fpath) and fname.endswith(".compute.glsl"):
                shader_name = fname.split(".")[0]
                shader_obj = Shader.load_compute(Shader.SL_GLSL, fpath)
                self._shaders[shader_name] = shader_obj

    def compute(self):
        """ Precomputes the scattering """

        self.debug("Precomputing ...")
        exec_cshader = self._handle.exec_compute_shader

        # Transmittance
        exec_cshader(
            self._shaders["transmittance"], {
                "dest": self._textures["transmittance"].get_texture()
            }, (self._trans_w, self._trans_h, 1))

        # Delta E
        exec_cshader(
            self._shaders["delta_e"], {
                "transmittanceSampler": self._textures["transmittance"].get_texture(),
                "dest": self._textures["delta_e"].get_texture()
            }, (self._sky_w, self._sky_h, 1))

        # Delta S
        exec_cshader(
            self._shaders["delta_sm_sr"], {
                "transmittanceSampler": self._textures["transmittance"].get_texture(),
                "destDeltaSR": self._textures["delta_sr"].get_texture(),
                "destDeltaSM": self._textures["delta_sm"].get_texture()
            }, (self._res_mu_s_nu, self._res_mu, self._res_r), (8, 8, 8))

        # Copy deltaE to irradiance texture
        exec_cshader(
            self._shaders["copy_irradiance"], {
                "k": 0.0,
                "deltaESampler": self._textures["delta_e"].get_texture(),
                "dest": self._textures["irradiance"].get_texture()
            }, (self._sky_w, self._sky_h, 1))

        # Copy delta s into inscatter texture
        exec_cshader(
            self._shaders["copy_inscatter"], {
                "deltaSRSampler": self._textures["delta_sr"].get_texture(),
                "deltaSMSampler": self._textures["delta_sm"].get_texture(),
                "dest": self._textures["inscatter"].get_texture()
            }, (self._res_mu_s_nu, self._res_mu, self._res_r), (8, 8, 8))

        for order in range(2, 5):
            first = order == 2

            # Delta J
            exec_cshader(
                self._shaders["delta_j"], {
                    "transmittanceSampler": self._textures["transmittance"].get_texture(),
                    "deltaSRSampler": self._textures["delta_sr"].get_texture(),
                    "deltaSMSampler": self._textures["delta_sm"].get_texture(),
                    "deltaESampler": self._textures["delta_e"].get_texture(),
                    "dest": self._textures["delta_j"].get_texture(),
                    "first": first
                }, (self._res_mu_s_nu, self._res_mu, self._res_r), (8, 8, 8))

            # Delta E
            exec_cshader(
                self._shaders["irradiance_n"], {
                    "transmittanceSampler": self._textures["transmittance"].get_texture(),
                    "deltaSRSampler": self._textures["delta_sr"].get_texture(),
                    "deltaSMSampler": self._textures["delta_sm"].get_texture(),
                    "dest": self._textures["delta_e"].get_texture(),
                    "first": first
                }, (self._sky_w, self._sky_h, 1))

            # Delta Sr
            exec_cshader(
                self._shaders["delta_sr"], {
                    "transmittanceSampler": self._textures["transmittance"].get_texture(),
                    "deltaJSampler": self._textures["delta_j"].get_texture(),
                    "dest": self._textures["delta_sr"].get_texture(),
                    "first": first
                }, (self._res_mu_s_nu, self._res_mu, self._res_r), (8, 8, 8))

            # Add delta E to irradiance
            exec_cshader(
                self._shaders["add_delta_e"], {
                    "deltaESampler": self._textures["delta_e"].get_texture(),
                    "dest": self._textures["irradiance"].get_texture(),
                }, (self._sky_w, self._sky_h, 1))

            # Add deltaSr to inscatter texture
            exec_cshader(
                self._shaders["add_delta_sr"], {
                    "deltaSSampler": self._textures["delta_sr"].get_texture(),
                    "dest": self._textures["inscatter"].get_texture()
                }, (self._res_mu_s_nu, self._res_mu, self._res_r), (8, 8, 8))

        # Make stages available
        self._handle._display_stage.set_shader_input(
            "InscatterSampler", self._textures["inscatter"].get_texture())
        self._handle._display_stage.set_shader_input(
            "TransmittanceSampler", self._textures["transmittance"].get_texture())
        self._handle._display_stage.set_shader_input(
            "IrradianceSampler", self._textures["irradiance"].get_texture())
