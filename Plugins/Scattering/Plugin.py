
import os

# Load plugin api
from .. import *


from panda3d.core import Texture, Shader
from .ScatteringStage import ScatteringStage

# Create the main plugin
class Plugin(BasePlugin):

    def __init__(self, pipeline):
        BasePlugin.__init__(self, pipeline)

        # Init sizes, those should match with the ones specified in common.glsl
        self._trans_w, self._trans_h = 256 * 4, 64 * 4
        self._sky_w, self._sky_h = 64 * 4, 16 * 4
        self._res_r, self._res_mu, self._res_mu_s, self._res_nu = 32, 128, 32, 8
        self._res_mu_s_nu = self._res_mu_s * self._res_nu

    @PluginHook("on_pipeline_created")
    def on_create(self):
        self._create_textures()
        self._create_shaders()
        self._precompute()

    @PluginHook("on_stage_setup")
    def on_setup(self):
        self.debug("Setting up scattering stage ..")
        self._display_stage = self.create_stage(ScatteringStage)

    @PluginHook("on_shader_reload")
    def on_shader_reload(self):
        self._create_shaders()
        self._precompute()

    def _create_textures(self):
        """ Creates all the required textures """

        self._textures = {
            "transmittance": Image.create_2d("scattering-trans", 
                self._trans_w, self._trans_h, Texture.T_float, Texture.F_rgba32),

            "irradiance": Image.create_2d("scattering-irr", 
                self._sky_w, self._sky_h, Texture.T_float, Texture.F_rgba32),

            "inscatter": Image.create_3d("scattering-insc", 
                self._res_mu_s_nu, self._res_mu, self._res_r, Texture.T_float, Texture.F_rgba32),

            "delta_e": Image.create_2d("scattering-dx-e", 
                self._sky_w, self._sky_h, Texture.T_float, Texture.F_rgba32),

            "delta_sr": Image.create_3d("scattering-dx-sr", 
                self._res_mu_s_nu, self._res_mu, self._res_r, Texture.T_float, Texture.F_rgba32),

            "delta_sm": Image.create_3d("scattering-dx-sm", 
                self._res_mu_s_nu, self._res_mu, self._res_r, Texture.T_float, Texture.F_rgba32),

            "delta_j": Image.create_3d("scattering-dx-j", 
                self._res_mu_s_nu, self._res_mu, self._res_r, Texture.T_float, Texture.F_rgba32)
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

        resource_path = self.get_shader_resource("")
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
            }, (self._trans_w, self._trans_h, 1))

        # Delta E
        self.exec_compute_shader(self._shaders["delta_e"], {
                "transmittanceSampler": self._textures["transmittance"].get_texture(),
                "dest": self._textures["delta_e"].get_texture()
            }, (self._sky_w, self._sky_h, 1))

        # Delta S
        self.exec_compute_shader(self._shaders["delta_sm_sr"], {
                "transmittanceSampler": self._textures["transmittance"].get_texture(),
                "destDeltaSR": self._textures["delta_sr"].get_texture(),
                "destDeltaSM": self._textures["delta_sm"].get_texture()
            }, (self._res_mu_s_nu, self._res_mu, self._res_r), (8, 8, 8))

        # Copy deltaE to irradiance texture
        self.exec_compute_shader(self._shaders["copy_irradiance"], {
                "k": 0.0,
                "deltaESampler": self._textures["delta_e"].get_texture(),
                "dest": self._textures["irradiance"].get_texture()
            }, (self._sky_w, self._sky_h, 1))

        # Copy delta s into inscatter texture
        self.exec_compute_shader(self._shaders["copy_inscatter"], {
                "deltaSRSampler": self._textures["delta_sr"].get_texture(),
                "deltaSMSampler": self._textures["delta_sm"].get_texture(),
                "dest": self._textures["inscatter"].get_texture()
            }, (self._res_mu_s_nu, self._res_mu, self._res_r), (8, 8, 8))

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
                }, (self._res_mu_s_nu, self._res_mu, self._res_r), (8, 8, 8))

            # Delta E
            self.exec_compute_shader(self._shaders["irradiance_n"], {
                    "transmittanceSampler": self._textures["transmittance"].get_texture(),
                    "deltaSRSampler": self._textures["delta_sr"].get_texture(),
                    "deltaSMSampler": self._textures["delta_sm"].get_texture(),
                    "dest": self._textures["delta_e"].get_texture(),
                    "first": first
                }, (self._sky_w, self._sky_h, 1))

            # Delta Sr
            self.exec_compute_shader(self._shaders["delta_sr"], {
                    "transmittanceSampler": self._textures["transmittance"].get_texture(),
                    "deltaJSampler": self._textures["delta_j"].get_texture(),
                    "dest": self._textures["delta_sr"].get_texture(),
                    "first": first
                }, (self._res_mu_s_nu, self._res_mu, self._res_r), (8, 8, 8))

            # Add delta E to irradiance
            self.exec_compute_shader(self._shaders["add_delta_e"], {
                    "deltaESampler": self._textures["delta_e"].get_texture(),
                    "dest": self._textures["irradiance"].get_texture(),
                }, (self._sky_w, self._sky_h, 1))

            # Add deltaSr to inscatter texture
            self.exec_compute_shader(self._shaders["add_delta_sr"], {
                    "deltaSSampler": self._textures["delta_sr"].get_texture(),
                    "dest": self._textures["inscatter"].get_texture()
                }, (self._res_mu_s_nu, self._res_mu, self._res_r), (8, 8, 8))

        # Make stages available
        self._display_stage.set_shader_input("inscatterSampler",
            self._textures["inscatter"].get_texture())
        self._display_stage.set_shader_input("transmittanceSampler",
            self._textures["transmittance"].get_texture())
        self._display_stage.set_shader_input("irradianceSampler",
            self._textures["irradiance"].get_texture())
