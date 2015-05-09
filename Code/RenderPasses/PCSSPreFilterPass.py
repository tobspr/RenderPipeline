
from panda3d.core import NodePath, Shader, LVecBase2i, Texture, GeomEnums, Vec3
from panda3d.core import Camera, OrthographicLens, CullFaceAttrib, DepthTestAttrib
from panda3d.core import SamplerState, Vec4

from Code.Globals import Globals
from Code.RenderPass import RenderPass
from Code.RenderTarget import RenderTarget
from Code.MemoryMonitor import MemoryMonitor

class PCSSPreFilterPass(RenderPass):

    """ This pass prefilters the pcss shadows to speedup the lighting computation """

    def __init__(self):
        RenderPass.__init__(self)

    def getID(self):
        return "PCSSPreFilterPass"

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
        # Not much to be done here, most is done in the shader
        self.target = RenderTarget("PCSSPreFilter")
        self.target.setHalfResolution()
        self.target.addColorTexture()
        self.target.prepareOffscreenBuffer()

        self.blurTarget = RenderTarget("PCSSBlur")
        self.blurTarget.addColorTexture()
        self.blurTarget.prepareOffscreenBuffer()

        for target in [self.target, self.blurTarget]:
            target.getColorTexture().setMinfilter(SamplerState.FTNearest)
            target.getColorTexture().setMagfilter(SamplerState.FTNearest)

        self.blurTarget.setShaderInput("blurSourceTex", self.target.getColorTexture())

    def setShaders(self):
        shaderFilter = Shader.load(Shader.SLGLSL, 
            "Shader/DefaultPostProcess.vertex",
            "Shader/PCSSPreFilter.fragment")
        self.target.setShader(shaderFilter)

        shaderBlur = Shader.load(Shader.SLGLSL, 
            "Shader/DefaultPostProcess.vertex",
            "Shader/PCSSPreFilterBlur.fragment")
        self.blurTarget.setShader(shaderBlur)

        return [shaderFilter, shaderBlur]

    def setShaderInput(self, name, value, *args):
        self.target.setShaderInput(name, value, *args)
        self.blurTarget.setShaderInput(name, value, *args)

    def getOutputs(self):
        return {
            "PCSSPreFilterPass.resultTex": lambda: self.blurTarget.getColorTexture(),
        }

