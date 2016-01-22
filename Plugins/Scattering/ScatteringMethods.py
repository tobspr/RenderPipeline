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

from six.moves import range

from direct.stdpy.file import listdir, isfile, join
from panda3d.core import Texture, SamplerState, Shader

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
        lut_tex.set_wrap_u(SamplerState.WM_repeat)
        lut_tex.set_wrap_v(SamplerState.WM_clamp)
        lut_tex.set_wrap_w(SamplerState.WM_clamp)
        lut_tex.set_minfilter(SamplerState.FT_linear)
        lut_tex.set_magfilter(SamplerState.FT_linear)
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
                Texture.T_float, Texture.F_rgba16),

            "irradiance": Image.create_2d(
                "scattering-irradiance", self._sky_w, self._sky_h, Texture.T_float,
                Texture.F_rgba16),

            "inscatter": Image.create_3d(
                "scattering-inscatter", self._res_mu_s_nu, self._res_mu, self._res_r,
                Texture.T_float, Texture.F_rgba16),

            "delta_e": Image.create_2d(
                "scattering-dx-e", self._sky_w, self._sky_h, Texture.T_float,
                Texture.F_rgba16),

            "delta_sr": Image.create_3d(
                "scattering-dx-sr", self._res_mu_s_nu, self._res_mu, self._res_r,
                Texture.T_float, Texture.F_rgba16),

            "delta_sm": Image.create_3d(
                "scattering-dx-sm", self._res_mu_s_nu, self._res_mu, self._res_r,
                Texture.T_float, Texture.F_rgba16),

            "delta_j": Image.create_3d(
                "scattering-dx-j", self._res_mu_s_nu, self._res_mu, self._res_r,
                Texture.T_float, Texture.F_rgba16),
        }

        for img in self._textures.values():
            img.set_minfilter(SamplerState.FT_linear)
            img.set_magfilter(SamplerState.FT_linear)
            img.set_wrap_u(SamplerState.WM_clamp)
            img.set_wrap_v(SamplerState.WM_clamp)
            img.set_wrap_w(SamplerState.WM_clamp)

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
                "dest": self._textures["transmittance"]
            }, (self._trans_w, self._trans_h, 1))

        # Delta E
        exec_cshader(
            self._shaders["delta_e"], {
                "transmittanceSampler": self._textures["transmittance"],
                "dest": self._textures["delta_e"]
            }, (self._sky_w, self._sky_h, 1))

        # Delta S
        exec_cshader(
            self._shaders["delta_sm_sr"], {
                "transmittanceSampler": self._textures["transmittance"],
                "destDeltaSR": self._textures["delta_sr"],
                "destDeltaSM": self._textures["delta_sm"]
            }, (self._res_mu_s_nu, self._res_mu, self._res_r), (8, 8, 8))

        # Copy deltaE to irradiance texture
        exec_cshader(
            self._shaders["copy_irradiance"], {
                "k": 0.0,
                "deltaESampler": self._textures["delta_e"],
                "dest": self._textures["irradiance"]
            }, (self._sky_w, self._sky_h, 1))

        # Copy delta s into inscatter texture
        exec_cshader(
            self._shaders["copy_inscatter"], {
                "deltaSRSampler": self._textures["delta_sr"],
                "deltaSMSampler": self._textures["delta_sm"],
                "dest": self._textures["inscatter"]
            }, (self._res_mu_s_nu, self._res_mu, self._res_r), (8, 8, 8))

        for order in range(2, 5):
            first = order == 2

            # Delta J
            exec_cshader(
                self._shaders["delta_j"], {
                    "transmittanceSampler": self._textures["transmittance"],
                    "deltaSRSampler": self._textures["delta_sr"],
                    "deltaSMSampler": self._textures["delta_sm"],
                    "deltaESampler": self._textures["delta_e"],
                    "dest": self._textures["delta_j"],
                    "first": first
                }, (self._res_mu_s_nu, self._res_mu, self._res_r), (8, 8, 8))

            # Delta E
            exec_cshader(
                self._shaders["irradiance_n"], {
                    "transmittanceSampler": self._textures["transmittance"],
                    "deltaSRSampler": self._textures["delta_sr"],
                    "deltaSMSampler": self._textures["delta_sm"],
                    "dest": self._textures["delta_e"],
                    "first": first
                }, (self._sky_w, self._sky_h, 1))

            # Delta Sr
            exec_cshader(
                self._shaders["delta_sr"], {
                    "transmittanceSampler": self._textures["transmittance"],
                    "deltaJSampler": self._textures["delta_j"],
                    "dest": self._textures["delta_sr"],
                    "first": first
                }, (self._res_mu_s_nu, self._res_mu, self._res_r), (8, 8, 8))

            # Add delta E to irradiance
            exec_cshader(
                self._shaders["add_delta_e"], {
                    "deltaESampler": self._textures["delta_e"],
                    "dest": self._textures["irradiance"],
                }, (self._sky_w, self._sky_h, 1))

            # Add deltaSr to inscatter texture
            exec_cshader(
                self._shaders["add_delta_sr"], {
                    "deltaSSampler": self._textures["delta_sr"],
                    "dest": self._textures["inscatter"]
                }, (self._res_mu_s_nu, self._res_mu, self._res_r), (8, 8, 8))

        # Make stages available
        self._handle._display_stage.set_shader_input(
            "InscatterSampler", self._textures["inscatter"])
        self._handle._display_stage.set_shader_input(
            "transmittanceSampler", self._textures["transmittance"])
        self._handle._display_stage.set_shader_input(
            "IrradianceSampler", self._textures["irradiance"])
