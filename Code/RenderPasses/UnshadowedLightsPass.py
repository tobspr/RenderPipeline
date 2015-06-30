
from panda3d.core import NodePath, Shader, LVecBase2i, Texture, GeomEnums

from ..Globals import Globals
from ..RenderPass import RenderPass
from ..RenderTarget import RenderTarget

class UnshadowedLightsPass(RenderPass):

    """ This pass processes all lights which have no shadows """

    def __init__(self):
        RenderPass.__init__(self)

    def getID(self):
        return "UnshadowedLightsPass"

    def getRequiredInputs(self):
        return {

            # Deferred target
            "data0": "DeferredScenePass.data0",
            "data1": "DeferredScenePass.data1",
            "data2": "DeferredScenePass.data2",
            "data3": "DeferredScenePass.data3",
            "depth": "DeferredScenePass.depth",


            # Lighting
            "lightsPerTileBuffer": "LightCullingPass.lightsPerTile",
            "lightingTileCount": "Variables.lightingTileCount",
            "lights": "Variables.allLights",

            # IES Profiles
            "IESProfilesTex": "Variables.IESProfilesTex",


            "cameraPosition": "Variables.cameraPosition",
            "mainCam": "Variables.mainCam",
            "mainRender": "Variables.mainRender"

        }

    def create(self):
        self.target = RenderTarget("Unshadowed Lights")
        self.target.addColorTexture()
        self.target.setColorBits(16)
        self.target.prepareOffscreenBuffer()
        self.target.setClearColor()
 
    def setShaders(self):
        shader = Shader.load(Shader.SLGLSL, 
            "Shader/DefaultPostProcess.vertex",
            "Shader/UnshadowedLightsPass.fragment")
        self.target.setShader(shader)
        return [shader]

    def getOutputs(self):
        return {
            "UnshadowedLightsPass.resultTex": lambda: self.target.getColorTexture(),
        }
