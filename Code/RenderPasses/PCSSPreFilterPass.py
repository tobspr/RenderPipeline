
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


        self.blurTargetV = RenderTarget("PCSSBlurV")
        self.blurTargetV.addColorTexture()
        self.blurTargetV.prepareOffscreenBuffer()

        self.blurTargetH = RenderTarget("PCSSBlurH")
        self.blurTargetH.addColorTexture()
        self.blurTargetH.prepareOffscreenBuffer()

        self.blurTargetV.setShaderInput("blurSourceTex", self.target.getColorTexture())
        self.blurTargetH.setShaderInput("blurSourceTex", self.blurTargetV.getColorTexture())

    def setShaders(self):
        shader = Shader.load(Shader.SLGLSL, 
            "Shader/DefaultPostProcess.vertex",
            "Shader/PCSSPreFilter.fragment")
        self.target.setShader(shader)

        shader = Shader.load(Shader.SLGLSL, 
            "Shader/DefaultPostProcess.vertex",
            "Shader/PCSSPreFilterBlurV.fragment")
        self.blurTargetV.setShader(shader)

        shader = Shader.load(Shader.SLGLSL, 
            "Shader/DefaultPostProcess.vertex",
            "Shader/PCSSPreFilterBlurH.fragment")
        self.blurTargetH.setShader(shader)

    def setShaderInput(self, name, value, *args):
        self.target.setShaderInput(name, value, *args)
        self.blurTargetV.setShaderInput(name, value, *args)
        self.blurTargetH.setShaderInput(name, value, *args)

    def getOutputs(self):
        return {
            "PCSSPreFilterPass.resultTex": lambda: self.blurTargetH.getColorTexture(),
        }

