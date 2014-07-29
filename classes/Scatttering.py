

from panda3d.core import Vec3, ShaderAttrib, NodePath, Texture
from BetterShader import BetterShader
from DebugObject import DebugObject
from Globals import Globals
from RenderTarget import RenderTarget
from TextureDebugger import TextureDebugger


class Scattering(DebugObject):

    """ This class provides functions to precompute and apply
    atmospheric scattering """

    def __init__(self):
        """ Creates a new Scattering object with default settings """
        DebugObject.__init__(self, "AtmosphericScattering")

        self.settings = {
            "radiusGround": 6360.0,
            "radiusAtmosphere": 6420.0,
            "radiusAtmosphere1": 6421.0,
            "averageGroundReflectance": 0.1,   # AVERAGE_GROUND_REFLECTANCE
            "rayleighFactor": 8.0,  # HR
            "betaRayleigh": Vec3(5.8e-3, 1.35e-2, 3.31e-2),  # betaR
            "mieFactor": 3.0,  # HM
            "betaMieScattering": Vec3(2e-3),  # betaMSca
            # betaMSca
            "betaMieScatteringAdjusted": (Vec3(2e-3) * 1.1111111111),
            "mieG": 0.8,  # mieG
            "transmittanceNonLinear": True,
            "inscatterNonLinear": True,
        }

        self.targets = {}
        self.textures = {}

    def _executePrecompute(self):
        """ Executes the precomputation for the scattering """

        # Transmittance
        self.targets['transmittance'] = self._createRT(
            "Transmittance", 256, 64, aux=False, shaderName="Transmittance", layers=1)
        self._renderOneShot('transmittance')

        # Irradiance1 (Produces DeltaE Texture)
        self.targets['irradiance1'] = self._createRT(
            "Irradiance1", 64, 16, aux=False, shaderName="Irradiance1", layers=1)
        self._renderOneShot('irradiance1')

        # Delta Scattering (Rayleigh + Mie)
        self.targets['deltaScattering'] = self._createRT(
            "DeltaScattering", 256, 128, aux=True, shaderName="Inscatter1", layers=32)
        self._renderOneShot('deltaScattering')

        # IrradianceE (Produces E Texture)
        self.targets['irradianceE'] = self._createRT(
            "IrradianceE", 64, 16, aux=False, shaderName="Combine2DTextures", layers=1)
        self.targets['irradianceE'].setShaderInput('factor1', 0.0)
        self.targets['irradianceE'].setShaderInput('factor2', 0.0)

        # Copy delta scattering into inscatter texture S
        self.targets['combinedDeltaScattering'] = self._createRT(
            "CombinedDeltaScattering", 256, 128, aux=False, shaderName="CombineDeltaScattering", layers=32)
        self._renderOneShot('combinedDeltaScattering')


        first = True
        passIndex = "Pass0"

        # Compute Delta J texture
        inscatterSName = 'inscatterS' + passIndex
        self.targets[inscatterSName] = self._createRT(
            inscatterSName, 256, 128, aux=False, shaderName="InscatterS", layers=32)
        self.targets[inscatterSName].setShaderInput("first", True)
        self._renderOneShot(inscatterSName)

        

        # computes deltaJ
        # tx_deltaJ = Texture()
        # setupLayers(tx_deltaJ, layer_count)
        # self.prepareTexture(tx_deltaJ)
        # quad,buf = self.allocateBuffer(256,128, tx_deltaJ, GraphicsOutput.RTMBindLayered)
        # quad.setShaderInput("first", first)
        # quad.setShaderInput("tx_transmittance", tx_T)
        # quad.setShaderInput("deltaESampler", tx_deltaE)
        # quad.setShaderInput("deltaSRSampler", tx_deltaSR)
        # quad.setShaderInput("deltaSMSampler", tx_deltaSM)
        # quad.setShader(prog_inscatterS)
        # handleBuffer(buf, tx_deltaJ)
        # writeTex(tx_deltaJ, "deltaJ_"+str(order))




        self._renderOneShot('irradianceE')

    def _renderOneShot(self, targetName):
        """ Renders a target and then deletes the target """
        target = self.targets[targetName]
        target.setActive(True)
        Globals.base.graphicsEngine.renderFrame()
        target.setActive(False)
        target.deleteBuffer()

    def _createRT(self, name, w, h, aux=False, shaderName="", layers=1):

        print "Create RT",name
        """ Internal shortcut to create a new render target """
        rt = RenderTarget("Scattering" + name)
        rt.setSize(w, h)
        rt.addColorTexture()
        rt.setColorBits(16)

        if aux:
            rt.addAuxTextures(1)
            rt.setAuxBits(16)

        if layers > 1:
            rt.setLayers(layers)
        rt.prepareOffscreenBuffer()

        sArgs = [
            "Shader/Scattering/DefaultVertex.vertex",
            "Shader/Scattering/" + shaderName + ".fragment"
        ]

        if layers > 1:
            sArgs.append("Shader/Scattering/DefaultGeometry.geometry")
        shader = BetterShader.load(*sArgs)
        rt.setShader(shader)

        self._setInputs(rt, "options.")


        for key, tex in self.textures.items():
            texName = key[0].lower() + key[1:]
            print "\tSetShaderInput:", texName, tex.getXSize(),"x",tex.getYSize(),"x",tex.getZSize()
            rt.setShaderInput(texName, tex)

        self.textures[name + "Color"] = rt.getColorTexture()

        if aux:
            self.textures[name + "Aux"] = rt.getAuxTexture(0)


        return rt

    def _setInputs(self, node, prefix):
        """ Sets all necessary inputs on a render target """
        for key, val in self.settings.items():

            node.setShaderInput(prefix + key, val)

    def precompute(self):
        """ Precomputes the scattering. This is required before you can use it """
        self.debug("Precomputing ..")

        self._executePrecompute()

        # write out transmittance tex

        debg = TextureDebugger()

        for key, tex in self.textures.items():
            base.graphicsEngine.extract_texture_data(
                tex, Globals.base.win.getGsg())

            dest = "Data/Scattering/" + key + ".png"
            if tex.getZSize() > 1:
                debg.debug3DTexture(tex, dest)
            else:
                tex.write(dest)

    def setSettings(self, settings):
        """ Sets the settings used for the precomputation """
        self.warn("Todo: Implement setSettings")
