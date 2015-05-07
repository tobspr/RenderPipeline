
from panda3d.core import NodePath, Shader, LVecBase2i, Texture, GeomEnums, Vec3
from panda3d.core import Camera, OrthographicLens, CullFaceAttrib, DepthTestAttrib
from panda3d.core import SamplerState, Vec4

from Code.Globals import Globals
from Code.RenderPass import RenderPass
from Code.RenderTarget import RenderTarget
from Code.MemoryMonitor import MemoryMonitor

class LightingPass(RenderPass):

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
            "giDiffuseTex": ["EdgePreservingBlurPass.blurResult", "Variables.emptyTextureWhite"],
            "giReflectionTex": ["EdgePreservingBlurPass.blurResult", "Variables.emptyTextureWhite"],
            "occlusionTex": ["EdgePreservingBlurPass.blurResult", "Variables.emptyTextureWhite"],
            "blurredGiandAoTex": ["EdgePreservingBlurPass.blurResult", "Variables.emptyTextureWhite"],

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
            "dynamicExposureTex": "Variables.dynamicExposureTex", #TODO

            # Scattering
            "transmittanceSampler": "Variables.transmittanceSampler",
            "inscatterSampler": "Variables.inscatterSampler",
            "scatteringOptions": "Variables.scatteringOptions",

            # Default environment
            "fallbackCubemap": "Variables.defaultEnvironmentCubemap",
            "fallbackCubemapMipmaps": "Variables.defaultEnvironmentCubemapMipmaps",




            # Scene data
            "noiseTexture": "Variables.noise4x4",
            "cameraPosition": "Variables.cameraPosition",
            "mainCam": "Variables.mainCam",
            "mainRender": "Variables.mainRender"
        }

    def create(self):

        self.target = RenderTarget("LightingPass")
        self.target.addColorTexture()
        self.target.setColorBits(16)
        self.target.prepareOffscreenBuffer()


    def setShaders(self):
        shader = Shader.load(Shader.SLGLSL, 
            "Shader/DefaultPostProcess.vertex",
            "Shader/ApplyLighting.fragment")
        self.target.setShader(shader)

    def getOutputs(self):
        return {
            "LightingPass.resultTex": lambda: self.target.getColorTexture(),
        }

