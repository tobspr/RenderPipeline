
from panda3d.core import Vec3
from panda3d.core import Shader
from DebugObject import DebugObject
from Globals import Globals
from RenderTarget import RenderTarget
from panda3d.core import PTAFloat, PTALVecBase3f

from direct.stdpy.file import isdir

# need legacy makedirs here
from os import makedirs


class Scattering(DebugObject):

    """ This class provides functions to precompute and apply an atmospheric
    scattering model. """

    def __init__(self, pipeline):
        """ Creates a new Scattering object with default settings """
        DebugObject.__init__(self, "AtmosphericScattering")

        self.pipeline = pipeline
        self.settings = {
            "radiusGround": 6360.0,
            "radiusAtmosphere": 6420.0,
            "averageGroundReflectance": 0.1, 
            "rayleighFactor": 8.0,
            "betaRayleigh": Vec3(5.8e-3, 1.35e-2, 3.31e-2),
            "mieFactor": 1.2,
            "betaMieScattering": Vec3(4e-3),
            "betaMieScatteringAdjusted": (Vec3(2e-3) * (1.0 / 0.9)),
            "mieG": 0.8,
            "transmittanceNonLinear": True,
            "inscatterNonLinear": True,
            "atmosphereOffset": Vec3(0),
            "atmosphereScale": Vec3(1)
        }

        # Store all parameters in a pta, that is faster than using setShaderInput
        self.settingsPTA = {}
        self.targets = {}
        self.textures = {}
        self.precomputed = False

    def _generatePTAs(self):
        """ Converts all settings to pta arrays, this is faster than using
        setShaderInput for every uniform """
        for settingName, settingValue in self.settings.items():
            if type(settingValue) == float:
                self.settingsPTA[settingName] = PTAFloat.emptyArray(1)
                self.settingsPTA[settingName][0] = settingValue
            elif type(settingValue) == Vec3:
                self.settingsPTA[settingName] = PTALVecBase3f.emptyArray(1)
                self.settingsPTA[settingName][0] = settingValue
            elif type(settingValue) == bool:
                self.settingsPTA[settingName] = settingValue
            else:
                self.warn("Unkown type:", settingName, type(settingValue))

    def adjustSetting(self, name, value):
        """ This function can be used to adjust a scattering setting after 
        precomputing. """

        if not self.precomputed:
            self.warn("Cannot use adjustSetting when not precomputed yet")
            return

        if name in self.settingsPTA:
            if type(value) not in [float, Vec3]:
                self.warn("You cannot change this value at runtime. "
                          "Only floats and vec3 are supported.")
                return
            self.settingsPTA[name][0] = value

    def _executePrecompute(self):
        """ Executes the precomputation for the scattering. This disables all 
        windows/regions first, executes the scattering, and then reenables them.
        This ensure no errors are thrown during the generation because of missing
        shader inputs.

        To render the targets, base.graphicsEngine.renderFrame() is called several
        times. For this reason, scattering should be precomputed before the actual
        scene got loaded, or the precompute time will increase, depending on the
        scene complexity. """

        # Disable all display regions - otherwise the shader inputs are
        # required too early
        disabledWindows = []
        for window in Globals.base.graphicsEngine.getWindows():
            window.setActive(False)
            disabledWindows.append(window)

        # Create PTAs
        self._generatePTAs()

        self.debug("Disabled", len(disabledWindows), " windows while rendering")

        # Transmittance
        self.targets['transmittance'] = self._createRT(
            "Transmittance", 256, 64, aux=False, shaderName="Transmittance",
            layers=1)
        self._renderOneShot('transmittance')

        # Irradiance1 (Produces DeltaE Texture)
        self.targets['irradiance1'] = self._createRT(
            "Irradiance1", 64, 16, aux=False, shaderName="Irradiance1",
            layers=1)
        self._renderOneShot('irradiance1')

        # Delta Scattering (Rayleigh + Mie)
        self.targets['deltaScattering'] = self._createRT(
            "DeltaScattering", 256, 128, aux=True, shaderName="Inscatter1",
            layers=32)
        self._renderOneShot('deltaScattering')

        # IrradianceE (Produces E Texture)
        self.targets['irradianceE'] = self._createRT(
            "IrradianceE", 64, 16, aux=False, shaderName="Combine2DTextures",
            layers=1)
        self.targets['irradianceE'].setShaderInput('factor1', 0.0)
        self.targets['irradianceE'].setShaderInput('factor2', 0.0)
        self._renderOneShot('irradianceE')

        # Copy delta scattering into inscatter texture S
        self.targets['combinedDeltaScattering'] = self._createRT(
            "CombinedDeltaScattering", 256, 128, aux=False,
            shaderName="CombineDeltaScattering", layers=32)
        self._renderOneShot('combinedDeltaScattering')

        for i in xrange(3):
            first = i == 0
            passIndex = "Pass" + str(i)

            # Compute Delta J texture
            inscatterSName = 'inscatterS' + passIndex
            self.targets[inscatterSName] = self._createRT(
                inscatterSName, 256, 128, aux=False, shaderName="InscatterS",
                layers=32)
            self.targets[inscatterSName].setShaderInput("first", first)
            self._renderOneShot(inscatterSName)

            # Compute the new Delta E Texture
            irradianceNName = 'irradianceN' + passIndex
            self.targets[irradianceNName] = self._createRT(
                irradianceNName, 64, 16, aux=False, shaderName="IrradianceN",
                layers=1)
            self.targets[irradianceNName].setShaderInput('first', first)
            self._renderOneShot(irradianceNName)

            # Replace old delta E texture
            self.textures['irradiance1Color'] = self.textures[
                irradianceNName + "Color"]

            # Compute new deltaSR
            inscatterNName = 'inscatterN' + passIndex
            self.targets[inscatterNName] = self._createRT(
                inscatterNName, 256, 128, aux=False, shaderName="InscatterN",
                layers=32)
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
                irradianceAddName, 64, 16, aux=False,
                shaderName="Combine2DTextures", layers=1)
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
                inscatterAddName, 256, 128, aux=False,
                shaderName="InscatterAdd", layers=32)
            self.targets[inscatterAddName].setShaderInput("first", first)
            self.targets[inscatterAddName].setShaderInput(
                "deltaSSampler", self.textures["deltaScatteringColor"])
            self.targets[inscatterAddName].setShaderInput(
                "addSampler", self.textures["combinedDeltaScatteringColor"])
            self._renderOneShot(inscatterAddName)

            self.textures['combinedDeltaScatteringColor'] = self.textures[
                inscatterAddName + "Color"]

        # Store result textures as attributes
        self.inscatterResult = self.textures['combinedDeltaScatteringColor']
        self.transmittanceResult = self.textures['transmittanceColor']

        # Reenable the windows which were previously disabled
        for window in disabledWindows:
            window.setActive(True)

        self.debug("Finished precomputing, also reenabled windows.")
        self.precomputed = True

    def _renderOneShot(self, targetName):
        """ Renders a target and then deletes the target. This enables the target
        first, forces a frame render, and then disables and deletes the target. """
        target = self.targets[targetName]
        target.setActive(True)
        Globals.base.graphicsEngine.renderFrame()
        target.setActive(False)
        target.deleteBuffer()

    def _createRT(self, name, width, height, attachAuxTexture=False, shaderName="", layers=1):
        """ Internal shortcut to create a new render target. The name should be
        a unique identifier. When attachAuxTexture is True, an aux texture will
        be attached to the buffer, additionally to the color texture. 
        The shader name determines the shader to load for the target, see below.
        When layers is > 1, a layered render target will be created to render to
        a 3D texture."""

        # Setup the render target
        target = RenderTarget("Scattering" + name)
        target.setSize(width, height)
        target.addColorTexture()
        target.setColorBits(16)

        # Adds aux textures if specified
        if attachAuxTexture:
            target.addAuxTextures(1)
            target.setAuxBits(16)

        # Add render layers if specified
        if layers > 1:
            target.setLayers(layers)

        target.prepareOffscreenBuffer()

        # Load the appropriate shader
        sArgs = ["Shader/Scattering/DefaultVertex.vertex",
            "Shader/Scattering/" + shaderName + ".fragment"]

        # When using layered rendering, a geometry shader is required
        if layers > 1:
            sArgs.append("Shader/Scattering/DefaultGeometry.geometry")

        shader = Shader.load(Shader.SLGLSL, *sArgs)
        target.setShader(shader)

        # Make the scattering options available
        self._setInputs(target, "options")

        # Lowercase the first letter
        lowerCaseFirst = lambda x: x[0].lower() + x[1:]

        # Make all rendered textures so far available to the target
        for key, tex in self.textures.items():
            target.setShaderInput(key, tex)

        # Register the created textures
        self.textures[lowerCaseFirst(name) + "Color"] = target.getColorTexture()
        if attachAuxTexture:
            self.textures[lowerCaseFirst(name) + "Aux"] = target.getAuxTexture(0)
 
        return target

    def provideInputs(self):
        """ Registers the scattering variables to the render pass manger so they
        can be used in the lighting pass """

        self.pipeline.renderPassManager.registerStaticVariable(
            "transmittanceSampler", self.transmittanceResult)
        self.pipeline.renderPassManager.registerStaticVariable(
            "inscatterSampler", self.inscatterResult)
        self.pipeline.renderPassManager.registerDynamicVariable(
            "scatteringOptions", self.bindTo)

    def bindTo(self, node, prefix):
        """ Sets all necessary inputs to compute the scattering on a render target """
        if not self.precomputed:
            self.warn("You can only call bindTo after the scattering got "
                      "precomputed!")
            return
        self._setInputs(node, prefix)

    def _setInputs(self, node, prefix):
        """ Internal method to set necessary inputs on a render target """
        for key, val in self.settingsPTA.items():
            node.setShaderInput(prefix + "." + key, val)

    def precompute(self):
        """ Precomputes the scattering. This is required before you
        can use it """
        if self.precomputed:
            self.error("Scattering is already computed! You can only do this once")
            return
        self.debug("Precomputing ..")
        self._executePrecompute()

    def setSettings(self, settings):
        """ Sets the settings used for the precomputation. If a setting is not
        specified, the default is used """

        if self.precomputed:
            self.warn("You cannot use setSettings after precomputing! Use "
                      "adjustSetting instead!")
            return

        for key, val in settings.items():
            if key in self.settings:
                if type(val) == type(self.settings[key]):
                    self.settings[key] = val
                else:
                    self.warn(
                        "Wrong type for", key, "- should be", type(self.settings[key]))
            else:
                self.warn("Unrecognized setting:", key)
