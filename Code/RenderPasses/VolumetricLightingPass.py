
from panda3d.core import NodePath, Shader, LVecBase2i, Texture, GeomEnums, Vec3
from panda3d.core import Camera, OrthographicLens, CullFaceAttrib, DepthTestAttrib
from panda3d.core import SamplerState, Vec4

from ..Globals import Globals
from ..RenderPass import RenderPass
from ..RenderTarget import RenderTarget
from ..MemoryMonitor import MemoryMonitor

class VolumetricLightingPass(RenderPass):

    """ This pass computes volumetric lighting at half screen resolution """

    def __init__(self):
        RenderPass.__init__(self)

    def getID(self):
        return "VolumetricLightingPass"

    def getRequiredInputs(self):
        return {

            # Deferred target
            "wsPositionTex": "DeferredScenePass.wsPosition",
            "wsNormalTex": "DeferredScenePass.wsNormal",
            "depthTex": "DeferredScenePass.depth",

            # Lighting
            "lightsPerTileBuffer": "LightCullingPass.lightsPerTile",
            "lightingTileCount": "Variables.lightingTileCount",
            "lights": "Variables.allLights",
            "shadowAtlasPCF": "ShadowScenePass.atlasPCF",
            "shadowAtlas": "ShadowScenePass.atlas",
            "shadowSources": "Variables.allShadowSources",
            "cameraPosition": "Variables.cameraPosition",
            "mainCam": "Variables.mainCam",
            "mainRender": "Variables.mainRender"
        }

    def create(self):
        self.target = RenderTarget("Volumetric Lighting")
        self.target.setHalfResolution()
        self.target.addColorTexture()
        self.target.prepareOffscreenBuffer()

    def setShaders(self):
        shader = Shader.load(Shader.SLGLSL, 
            "Shader/DefaultPostProcess.vertex",
            "Shader/VolumetricLighting.fragment")
        self.target.setShader(shader)

        return [shader]

    def setShaderInput(self, name, value, *args):
        self.target.setShaderInput(name, value, *args)
        # self.blurTarget.setShaderInput(name, value, *args)

    def getOutputs(self):
        return {
            "VolumetricLightingPass.resultTex": lambda: self.target.getColorTexture(),
        }

