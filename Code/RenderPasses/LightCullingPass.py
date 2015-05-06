
from panda3d.core import NodePath, Shader, LVecBase2i, Texture, GeomEnums

from Code.Globals import Globals
from Code.RenderPass import RenderPass
from Code.RenderTarget import RenderTarget
from Code.LightLimits import LightLimits
from Code.MemoryMonitor import MemoryMonitor

class LightCullingPass(RenderPass):

    def __init__(self):
        RenderPass.__init__(self)

    def getID(self):
        return "LightCullingPass"

    def setSize(self, sizeX, sizeY):
        self.size = LVecBase2i(sizeX, sizeY)

    def setPatchSize(self, patchSizeX, patchSizeY):
        self.patchSize = LVecBase2i(patchSizeX, patchSizeY)

    def getRequiredInputs(self):
        return {
            "renderedLightsBuffer": "Variables.renderedLightsBuffer",
            "lights": "Variables.allLights",
            "mainCam": "Variables.mainCam",
            "mainRender": "Variables.mainRender"
        }

    def create(self):
        self.target = RenderTarget("ComputeLightTileBounds")
        self.target.setSize(self.size.x, self.size.y)
        self.target.addColorTexture()
        self.target.prepareOffscreenBuffer()

        self.makePerTileStorage()
        self.target.setShaderInput("destinationBuffer", self.lightPerTileBuffer)

    def makePerTileStorage(self):
        self.tileStride = 0
        self.tileStride += 16 # Counters for the light types
        
        self.tileStride += LightLimits.maxPerTileLights["PointLight"]
        self.tileStride += LightLimits.maxPerTileLights["PointLightShadow"]

        self.tileStride += LightLimits.maxPerTileLights["DirectionalLight"]
        self.tileStride += LightLimits.maxPerTileLights["DirectionalLightShadow"]
        
        self.tileStride += LightLimits.maxPerTileLights["SpotLight"]
        self.tileStride += LightLimits.maxPerTileLights["SpotLightShadow"]

        tileBufferSize = self.size.x * self.size.y * self.tileStride
        self.lightPerTileBuffer = Texture("LightsPerTileBuffer")
        self.lightPerTileBuffer.setupBufferTexture(
            tileBufferSize, Texture.TInt, Texture.FR32i, GeomEnums.UHDynamic)

        MemoryMonitor.addTexture("Light Per Tile Buffer", self.lightPerTileBuffer)

    def getDefines(self):
        return {
            "LIGHTING_PER_TILE_STRIDE": self.tileStride
        }
 
    def setShaders(self):
        pcShader = Shader.load(Shader.SLGLSL, 
            "Shader/DefaultPostProcess.vertex",
            "Shader/PrecomputeLights.fragment")
        self.target.setShader(pcShader)

    def getOutputs(self):
        return {
            "LightsPerTileBuffer": lambda: self.lightPerTileBuffer
        }

    def setShaderInput(self, name, value):
        self.target.setShaderInput(name, value)

