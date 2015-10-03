
from Util.SettingsLoader import SettingsLoader


class PipelineSettings(SettingsLoader):

    """ This class is a subclass of the SettingsLoader and
    stores the settings (and their defaults) used by RenderPipeline. """

    def __init__(self, pipeline):
        """ Constructs a new settings instance. Remember to call
        loadFromFile to load actual settings instead of the defaults. """
        SettingsLoader.__init__(self, "PipelineSettings", pipeline)

    def _add_default_settings(self):
        """ Internal method which populates the settings array with defaults
        and the internal type of settings (like int, bool, ...) """

        # [General]
        # self._add_setting("preventMultipleInstances", bool, False)
        # self._add_setting("resolution3D", float, 1.0)
        # self._add_setting("stateCacheClearInterval", float, 0.2)

        # [Rendering]
        # self._add_setting("enableEarlyZ", bool, True)

        # [Antialiasing]
        # self._add_setting("antialiasingTechnique", str, "SMAA")
        # self._add_setting("smaaQuality", str, "Low")
        # self._add_setting("jitterAmount", float, 1.0)

        # [Lighting]
        self._add_setting("lightGridSizeX", int, 32)
        self._add_setting("lightGridSizeY", int, 32)
        self._add_setting("lightGridSlices", int, 16)
        # self._add_setting("defaultReflectionCubemap", str, "Default-0/#.png")
        # self._add_setting("colorLookupTable", str, "Default.png")
        # self._add_setting("cubemapAntialiasingFactor", float, 5.0)
        # self._add_setting("useAdaptiveBrightness", bool, True)
        # self._add_setting("targetExposure", float, 0.8)
        # self._add_setting("brightnessAdaptionSpeed", float, 1.0)
        # self._add_setting("globalAmbientFactor", float, 1.0)
        # self._add_setting("useColorCorrection", bool, True)
        # self._add_setting("enableAlphaTestedShadows", bool, True)
        # self._add_setting("useDiffuseAntialiasing", bool, True)

        # [Scattering]
        # self._add_setting("enableScattering", bool, False)
        # self._add_setting("scatteringCubemapSize", int, 256)

        # [SSLR]
        # self._add_setting("enableSSLR", bool, True)
        # self._add_setting("sslrUseHalfRes", bool, False)
        # self._add_setting("sslrNumSteps", int, 32)
        # self._add_setting("sslrScreenRadius", float, 0.3)

        # [Occlusion]
        # self._add_setting("occlusionTechnique", str, "None")
        # self._add_setting("occlusionRadius", float, 1.0)
        # self._add_setting("occlusionStrength", float, 1.0)
        # self._add_setting("occlusionSampleCount", int, 16)
        # self._add_setting("useTemporalOcclusion", bool, True)
        # self._add_setting("useLowQualityBlur", bool, False)
        # self._add_setting("useOcclusionNoise", bool, True)

        # [Shadows]
        # self._add_setting("renderShadows", bool, True)
        # self._add_setting("shadowAtlasSize", int, 8192)
        # self._add_setting("shadowCascadeBorderPercentage", float, 0.1)
        # self._add_setting("maxShadowUpdatesPerFrame", int, 2)
        # self._add_setting("numPCFSamples", int, 64)
        # self._add_setting("usePCSS", bool, True)
        # self._add_setting("numPCSSSearchSamples", int, 32)
        # self._add_setting("numPCSSFilterSamples", int, 64)
        # self._add_setting("useHardwarePCF", bool, False)
        # self._add_setting("alwaysUpdateAllShadows", bool, False)
        # self._add_setting("pcssSampleRadius", float, 0.01)

        # [Transparency]
        # self._add_setting("useTransparency", bool, True)
        # self._add_setting("maxTransparencyLayers", int, 10)
        # self._add_setting("maxTransparencyRange", float, 100.0)
        # self._add_setting("transparencyBatchSize", int, 200)

        # [Motion blur]
        # self._add_setting("enableMotionBlur", bool, False)
        # self._add_setting("motionBlurSamples", int, 8)
        # self._add_setting("motionBlurFactor", float, 1.0)
        # self._add_setting("motionBlurDilatePixels", float, 10.0)

        # [Global Illumination]
        # self._add_setting("enableGlobalIllumination", bool, False)
        # self._add_setting("giVoxelGridSize", float, 100.0)
        # self._add_setting("giQualityLevel", str, "High")

        # [Clouds]
        # self._add_setting("enableClouds", bool, False)

        # [Bloom]
        # self._add_setting("enableBloom", bool, False)

        # [Depth of Field]
        # self._add_setting("enableDOF", bool, True)

        # [Debugging]
        # self._add_setting("displayOnscreenDebugger", bool, False)
        # self._add_setting("displayDebugStats", bool, True)
        # self._add_setting("displayPerformanceOverlay", bool, True)
        # self._add_setting("pipelineOutputLevel", str, "debug")
        # self._add_setting("useDebugAttachments", bool, False)
