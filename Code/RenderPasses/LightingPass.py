
from panda3d.core import NodePath, Shader, LVecBase2i, Texture, GeomEnums, Vec3
from panda3d.core import Camera, OrthographicLens, CullFaceAttrib, DepthTestAttrib
from panda3d.core import SamplerState, Vec4

from Code.Globals import Globals
from Code.RenderPass import RenderPass
from Code.RenderTarget import RenderTarget
from Code.MemoryMonitor import MemoryMonitor

class LightingPass(RenderPass):

    """ This is the main lighting pass, it combines the inpupts of almost all
    features to create a combined image. It handles the lighting, shadows and
    ambient factors. It also computes the scattering based on the precomputed
    scattering model if specified """

    def __init__(self):
        RenderPass.__init__(self)

    def getID(self):
        return "LightingPass"

    def getRequiredInputs(self):
        return {

            # Deferred target
            "data0": "DeferredScenePass.data0",
            "data1": "DeferredScenePass.data1",
            "data2": "DeferredScenePass.data2",
            "data3": "DeferredScenePass.data3",

            # GI and occlusion
            "giDiffuseTex": ["GlobalIlluminationPass.diffuseResult", "Variables.emptyTextureWhite"],
            "giReflectionTex": ["GlobalIlluminationPass.specularResult", "Variables.emptyTextureWhite"],
            "occlusionTex": ["OcclusionBlurPass.blurResult", "Variables.emptyTextureWhite"],

            "lastFramePosition": "Variables.emptyTextureWhite", #TODO
            "lastFrameOcclusion": "Variables.emptyTextureWhite", #TODO


            # Lighting
            "lightsPerTileBuffer": "LightCullingPass.lightsPerTile",
            "lightingTileCount": "Variables.lightingTileCount",
            "lights": "Variables.allLights",
            "shadowAtlasPCF": "ShadowScenePass.atlasPCF",
            "shadowAtlas": "ShadowScenePass.atlas",
            "shadowSources": "Variables.allShadowSources",
            "directionToFace": "Variables.directionToFaceLookup",

            # Dynamic exposure
            "dynamicExposureTex": ["Variables.dynamicExposureTex", "Variables.null"],

            # Scattering
            "transmittanceSampler": ["Variables.transmittanceSampler", "Variables.emptyTextureWhite"],
            "inscatterSampler": ["Variables.inscatterSampler", "Variables.emptyTextureWhite"],
            "scatteringOptions": ["Variables.scatteringOptions", "Variables.null"],

            # Default environment
            "fallbackCubemap": "Variables.defaultEnvironmentCubemap",
            "fallbackCubemapMipmaps": "Variables.defaultEnvironmentCubemapMipmaps",

            # Prefiltered pccs shadow
            "prefilteredPCSSTex": ["PCSSPreFilterPass.resultTex", "Variables.emptyTextureWhite"],

            # Volumetric lighting
            "volumetricLightingTex": ["VolumetricLightingPass.resultTex", "Variables.emptyTextureWhite"],

            # IES Profiles
            "IESProfilesTex": "Variables.IESProfilesTex",

            # Scene data
            "noiseTexture": "Variables.noise4x4",
            "cameraPosition": "Variables.cameraPosition",
            "mainCam": "Variables.mainCam",
            "mainRender": "Variables.mainRender"
        }

    def create(self):
        # Not much to be done here, most is done in the shader
        self.target = RenderTarget("LightingPass")
        self.target.addColorTexture()
        self.target.setColorBits(16)
        self.target.prepareOffscreenBuffer()

    def setShaders(self):
        shader = Shader.load(Shader.SLGLSL, 
            "Shader/DefaultPostProcess.vertex",
            "Shader/ApplyLighting.fragment")
        self.target.setShader(shader)

        return [shader]

    def getOutputs(self):
        return {
            "LightingPass.resultTex": lambda: self.target.getColorTexture(),
        }

