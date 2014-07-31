

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
            "averageGroundReflectance": 0.1,   # AVERAGE_GROUND_REFLECTANCE
            "rayleighFactor": 8.0,  # HR
            "betaRayleigh": Vec3(5.8e-3, 1.35e-2, 3.31e-2),  # betaR
            "mieFactor": 1.2,  # HM
            "betaMieScattering": Vec3(4e-3),  # betaMSca
            # betaMSca
            "betaMieScatteringAdjusted": (Vec3(2e-3) * (1.0 / 0.9)),
            "mieG": 0.8,  # mieG
            "transmittanceNonLinear": True,
            "inscatterNonLinear": True,
        }

        self.targets = {}
        self.textures = {}
        self.writeOutput = True

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
        self._renderOneShot('irradianceE')



        # Copy delta scattering into inscatter texture S
        self.targets['combinedDeltaScattering'] = self._createRT(
            "CombinedDeltaScattering", 256, 128, aux=False, shaderName="CombineDeltaScattering", layers=32)
        self._renderOneShot('combinedDeltaScattering')




        for i in xrange(3):
            first = i == 0
            passIndex = "Pass" + str(i)

            # Compute Delta J texture
            inscatterSName = 'inscatterS' + passIndex
            self.targets[inscatterSName] = self._createRT(
                inscatterSName, 256, 128, aux=False, shaderName="InscatterS", layers=32)
            self.targets[inscatterSName].setShaderInput("first", first)
            self._renderOneShot(inscatterSName)

            # Compute the new Delta E Texture
            irradianceNName = 'irradianceN' + passIndex
            self.targets[irradianceNName] = self._createRT(
                irradianceNName, 64, 16, aux=False, shaderName="IrradianceN", layers=1)
            self.targets[irradianceNName].setShaderInput('first', first)
            self._renderOneShot(irradianceNName)

            # Replace old delta E texture
            self.textures['irradiance1Color'] = self.textures[
                irradianceNName + "Color"]

            # Compute new deltaSR
            inscatterNName = 'inscatterN' + passIndex
            self.targets[inscatterNName] = self._createRT(
                inscatterNName, 256, 128, aux=False, shaderName="InscatterN", layers=32)
            self.targets[inscatterNName].setShaderInput("first", first)
            self.targets[inscatterNName].setShaderInput(
                "deltaJSampler", self.textures[inscatterSName + "Color"])
            self._renderOneShot(inscatterNName)

            # Replace old deltaSR texture
            self.textures['deltaScatteringColor'] = self.textures[
                inscatterNName + "Color"]

            # Add deltaE into irradiance texture E
            irradianceAddName = 'irradianceAdd' + passIndex
            self.targets[irradianceAddName] = self._createRT(
                irradianceAddName, 64, 16, aux=False, shaderName="Combine2DTextures", layers=1)
            self.targets[irradianceAddName].setShaderInput('first', first)
            self.targets[irradianceAddName].setShaderInput(
                'source1', self.textures['irradianceEColor'])
            self.targets[irradianceAddName].setShaderInput(
                'source2', self.textures['irradiance1Color'])
            self.targets[irradianceAddName].setShaderInput('factor1', 1.0)
            self.targets[irradianceAddName].setShaderInput('factor2', 1.0)
            self._renderOneShot(irradianceAddName)

            self.textures['irradianceEColor'] = self.textures[
                irradianceAddName + "Color"]

            # Add deltaS into inscatter texture S
            inscatterAddName = 'inscatterAdd' + passIndex
            self.targets[inscatterAddName] = self._createRT(
                inscatterAddName, 256, 128, aux=False, shaderName="InscatterAdd", layers=32)
            self.targets[inscatterAddName].setShaderInput("first", first)
            self.targets[inscatterAddName].setShaderInput(
                "deltaSSampler", self.textures["deltaScatteringColor"])
            self.targets[inscatterAddName].setShaderInput(
                "addSampler", self.textures["combinedDeltaScatteringColor"])
            self._renderOneShot(inscatterAddName)

            self.textures['combinedDeltaScatteringColor'] = self.textures[
                inscatterAddName + "Color"]

        self.inscatterResult = self.textures['combinedDeltaScatteringColor']
        self.irradianceResult = self.textures['irradianceEColor']

        if self.writeOutput:
            base.graphicsEngine.extract_texture_data(
                self.irradianceResult, Globals.base.win.getGsg())
            self.irradianceResult.write("Data/Scattering/Result_Irradiance.png")
            base.graphicsEngine.extract_texture_data(
                self.inscatterResult, Globals.base.win.getGsg())
            self.inscatterResult.write("Data/Scattering/Result_Inscatter.png")

    def _renderOneShot(self, targetName):
        """ Renders a target and then deletes the target """
        self.debug("Rendering", targetName)
        target = self.targets[targetName]
        target.setActive(True)
        Globals.base.graphicsEngine.renderFrame()
        target.setActive(False)


        write = [(targetName + "Color", target.getColorTexture())]

        if target.hasAuxTextures():
            write.append((targetName + "Aux", target.getAuxTexture(0)))

        if self.writeOutput:
            for texname, tex in write:
                base.graphicsEngine.extract_texture_data(
                    tex, Globals.base.win.getGsg())

                dest = "Data/Scattering/" + texname + ".png"
                if tex.getZSize() > 1:
                    self.debg.debug3DTexture(tex, dest)
                else:
                    tex.write(dest)

        target.deleteBuffer()

    def _createRT(self, name, w, h, aux=False, shaderName="", layers=1):
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

        lc = lambda x: x[0].lower() + x[1:]

        for key, tex in self.textures.items():
            rt.setShaderInput(lc(key), tex)

        self.textures[lc(name) + "Color"] = rt.getColorTexture()

        if aux:
            self.textures[lc(name) + "Aux"] = rt.getAuxTexture(0)

        return rt

    def _setInputs(self, node, prefix):
        """ Sets all necessary inputs on a render target """
        for key, val in self.settings.items():

            node.setShaderInput(prefix + key, val)

    def precompute(self):
        """ Precomputes the scattering. This is required before you can use it """
        self.debug("Precomputing ..")

        if self.writeOutput:
            self.debg = TextureDebugger()
        self._executePrecompute()

        # write out transmittance tex

    def setSettings(self, settings):
        """ Sets the settings used for the precomputation """
        self.warn("Todo: Implement setSettings")
