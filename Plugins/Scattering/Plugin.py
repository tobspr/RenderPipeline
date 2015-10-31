
import os

# Load plugin api
from .. import *


from panda3d.core import Texture, Shader
from ScatteringStage import ScatteringStage

# Create the main plugin
class Plugin(BasePlugin):

    NAME = "Scattering"
    DESCRIPTION = """ This plugin adds support for Atmospheric Scattering """
    SETTINGS = {
    }

    def __init__(self, pipeline):
        BasePlugin.__init__(self, pipeline)

        # Init sizes, those should match with the ones specified in common.glsl
        self.trans_w, self.trans_h = 256 * 4, 64 * 4
        self.sky_w, self.sky_h = 64 * 4, 16 * 4
        self.res_r, self.res_mu, self.res_mu_s, self.res_nu = 32, 128, 32, 8
        self.res_mu_s_nu = self.res_mu_s * self.res_nu

    @PluginHook("on_pipeline_create")
    def on_create(self):
        self._create_textures()
        self._create_shaders()
        self._precompute()


    @PluginHook("on_stage_setup")
    def on_setup(self):

        self.debug("Setting up scattering stage ..")
        self._display_stage = ScatteringStage(self._pipeline)
        self._pipeline.get_stage_mgr().add_stage(self._display_stage)

    @PluginHook("on_shader_reload")
    def on_shader_reload(self):
        self._create_shaders()
        self._precompute()

    def _create_textures(self):
        """ Creates all the required textures """

        self._textures = {
            "transmittance": Image.create_2d("scattering-trans", 
                self.trans_w, self. trans_h, Texture.T_float, Texture.F_rgba32),

            "irradiance": Image.create_2d("scattering-irr", 
                self.sky_w, self.sky_h, Texture.T_float, Texture.F_rgba32),

            "inscatter": Image.create_3d("scattering-insc", 
                self.res_mu_s_nu, self.res_mu, self.res_r, Texture.T_float, Texture.F_rgba32),

            "delta_e": Image.create_2d("scattering-dx-e", 
                self.sky_w, self.sky_h, Texture.T_float, Texture.F_rgba32),

            "delta_sr": Image.create_3d("scattering-dx-sr", 
                self.res_mu_s_nu, self.res_mu, self.res_r, Texture.T_float, Texture.F_rgba32),

            "delta_sm": Image.create_3d("scattering-dx-sm", 
                self.res_mu_s_nu, self.res_mu, self.res_r, Texture.T_float, Texture.F_rgba32),

            "delta_j": Image.create_3d("scattering-dx-j", 
                self.res_mu_s_nu, self.res_mu, self.res_r, Texture.T_float, Texture.F_rgba32)
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

        resource_path = self.get_resource("Shader/")
        for f in os.listdir(resource_path):
            fpath = os.path.join(resource_path, f)
            if os.path.isfile(fpath) and f.endswith(".compute.glsl"):
                shader_name = f.split(".")[0]
                shader_obj = Shader.load_compute(Shader.SL_GLSL, fpath)
                self._shaders[shader_name] = shader_obj

    def _precompute(self):
        """ Precomputes the scattering """

        self.debug("Precomputing ...")

        # Transmittance
        self.exec_compute_shader(self._shaders["transmittance"], {
                "dest": self._textures["transmittance"].get_texture()
            }, (self.trans_w, self.trans_h, 1))

        # self._textures["transmittance"].write(self.get_resource("Tex/transmittance.png"))

        # Delta E
        self.exec_compute_shader(self._shaders["delta_e"], {
                "transmittanceSampler": self._textures["transmittance"].get_texture(),
                "dest": self._textures["delta_e"].get_texture()
            }, (self.sky_w, self.sky_h, 1))

        # self._textures["delta_e"].write(self.get_resource("Tex/delta_e.png"))

        # Delta S
        self.exec_compute_shader(self._shaders["delta_sm_sr"], {
                "transmittanceSampler": self._textures["transmittance"].get_texture(),
                "destDeltaSR": self._textures["delta_sr"].get_texture(),
                "destDeltaSM": self._textures["delta_sm"].get_texture()
            }, (self.res_mu_s_nu, self.res_mu, self.res_r), (8, 8, 8))

        # self._textures["delta_sr"].write(self.get_resource("Tex/delta_sr_#.png"))
        # self._textures["delta_sm"].write(self.get_resource("Tex/delta_sm_#.png"))

        # Copy deltaE to irradiance texture
        self.exec_compute_shader(self._shaders["copy_irradiance"], {
                "k": 0.0,
                "deltaESampler": self._textures["delta_e"].get_texture(),
                "dest": self._textures["irradiance"].get_texture()
            }, (self.sky_w, self.sky_h, 1))

        # self._textures["irradiance"].write(self.get_resource("Tex/irradiance.png"))

        # Copy delta s into inscatter texture
        self.exec_compute_shader(self._shaders["copy_inscatter"], {
                "deltaSRSampler": self._textures["delta_sr"].get_texture(),
                "deltaSMSampler": self._textures["delta_sm"].get_texture(),
                "dest": self._textures["inscatter"].get_texture()
            }, (self.res_mu_s_nu, self.res_mu, self.res_r), (8, 8, 8))

        for order in range(2, 5):
            first = order == 2

            # Delta J
            self.exec_compute_shader(self._shaders["delta_j"], {
                    "transmittanceSampler": self._textures["transmittance"].get_texture(),
                    "deltaSRSampler": self._textures["delta_sr"].get_texture(),
                    "deltaSMSampler": self._textures["delta_sm"].get_texture(),
                    "deltaESampler": self._textures["delta_e"].get_texture(),
                    "dest": self._textures["delta_j"].get_texture(),
                    "first": first
                }, (self.res_mu_s_nu, self.res_mu, self.res_r), (8, 8, 8))

            # self._textures["delta_j"].write(self.get_resource("Tex/delta_j_i0_#.png"))

            # Delta E
            self.exec_compute_shader(self._shaders["irradiance_n"], {
                    "transmittanceSampler": self._textures["transmittance"].get_texture(),
                    "deltaSRSampler": self._textures["delta_sr"].get_texture(),
                    "deltaSMSampler": self._textures["delta_sm"].get_texture(),
                    "dest": self._textures["delta_e"].get_texture(),
                    "first": first
                }, (self.sky_w, self.sky_h, 1))

            # self._textures["delta_e"].write(self.get_resource("Tex/delta_e_i0.png"))

            # Delta Sr
            self.exec_compute_shader(self._shaders["delta_sr"], {
                    "transmittanceSampler": self._textures["transmittance"].get_texture(),
                    "deltaJSampler": self._textures["delta_j"].get_texture(),
                    "dest": self._textures["delta_sr"].get_texture(),
                    "first": first
                }, (self.res_mu_s_nu, self.res_mu, self.res_r), (8, 8, 8))

            # self._textures["delta_sr"].write(self.get_resource("Tex/delta_sr_i0_#.png"))

            # Add delta E to irradiance
            self.exec_compute_shader(self._shaders["add_delta_e"], {
                    "deltaESampler": self._textures["delta_e"].get_texture(),
                    "dest": self._textures["irradiance"].get_texture(),
                }, (self.sky_w, self.sky_h, 1))

            # self._textures["irradiance"].write(self.get_resource("Tex/irradiance_i0.png"))

            # Add deltaSr to inscatter texture
            self.exec_compute_shader(self._shaders["add_delta_sr"], {
                    "deltaSSampler": self._textures["delta_sr"].get_texture(),
                    "dest": self._textures["inscatter"].get_texture()
                }, (self.res_mu_s_nu, self.res_mu, self.res_r), (8, 8, 8))

            # self._textures["inscatter"].write(self.get_resource("Tex/inscatter_i0_#.png"))
        self._display_stage.set_shader_input("inscatterSampler", self._textures["inscatter"].get_texture())
        self._display_stage.set_shader_input("transmittanceSampler", self._textures["transmittance"].get_texture())
        self._display_stage.set_shader_input("irradianceSampler", self._textures["irradiance"].get_texture())
