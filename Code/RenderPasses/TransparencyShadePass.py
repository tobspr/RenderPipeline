
from panda3d.core import Shader

from ..Globals import Globals
from ..RenderPass import RenderPass
from ..RenderTarget import RenderTarget

class TransparencyShadePass(RenderPass):

    """ This pass reads the per pixel linked lists generated during the deferred
    scene pass and lights the transparent pixels """

    def __init__(self):
        RenderPass.__init__(self)
        self.batchSize = 100

    def getID(self):
        return "TransparencyShadePass"

    def setBatchSize(self, size):
        """ Sets the size of a batch in pixels """
        self.batchSize = size

    def getRequiredInputs(self):
        return {
            "sceneTex": "LightingPass.resultTex",
            "cameraPosition": "Variables.cameraPosition",
            "currentMVP": "Variables.currentMVP",
            "positionTex": "DeferredScenePass.wsPosition",
            "mainCam": "Variables.mainCam",
            "mainRender": "Variables.mainRender",
            "fallbackCubemap": "Variables.defaultEnvironmentCubemap",
            "fallbackCubemapMipmaps": "Variables.defaultEnvironmentCubemapMipmaps",
            "depthTex": "DeferredScenePass.depth",

            "pixelCountBuffer": "Variables.transpPixelCountBuffer",
            "spinLockBuffer": "Variables.transpSpinLockBuffer",
            "listHeadBuffer": "Variables.transpListHeadBuffer",
            "materialDataBuffer": "Variables.transpMaterialDataBuffer",

            "renderedLightsBuffer": "Variables.renderedLightsBuffer",

            # Default environment
            "fallbackCubemap": "Variables.defaultEnvironmentCubemap",
            "fallbackCubemapMipmaps": "Variables.defaultEnvironmentCubemapMipmaps",

            # Lighting
            "lights": "Variables.allLights",
            "shadowAtlasPCF": "ShadowScenePass.atlasPCF",
            "shadowAtlas": "ShadowScenePass.atlas",
            "shadowSources": "Variables.allShadowSources",
            "directionToFace": "Variables.directionToFaceLookup",

            # IES Profiles
            "IESProfilesTex": "Variables.IESProfilesTex",

            "cameraPosition": "Variables.cameraPosition",
            "mainCam": "Variables.mainCam",
            "mainRender": "Variables.mainRender"

        }

    def setShaders(self):
        shader = Shader.load(Shader.SLGLSL, 
            "Shader/TransparencyShade/vertex.glsl",
            "Shader/TransparencyShade/fragment.glsl",
            "Shader/TransparencyShade/geometry.glsl",
            )
        self.target.setShader(shader)

        return [shader]

    def create(self):
        self.target = RenderTarget("TransparencyShadePass")
        self.target.setSize(self.batchSize, self.batchSize)
        self.target.addColorTexture()
        self.target.prepareOffscreenBuffer()

    def getOutputs(self):
        return {
            "TransparencyShadePass.resultTex": lambda: self.target.getColorTexture(),
        }

