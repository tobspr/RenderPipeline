
from panda3d.core import NodePath, Shader, LVecBase2i, Texture, GeomEnums, SamplerState

from Code.Globals import Globals
from Code.RenderPass import RenderPass
from Code.RenderTarget import RenderTarget
from Code.LightLimits import LightLimits
from Code.MemoryMonitor import MemoryMonitor

class LightCullingPass(RenderPass):

    """ This pass takes a list of all rendered lights and performs light culling
    per tile. The result is stored in a buffer which then can be used by the lighting
    pass to render the lights.

    The buffer maps 1 pixel per tile, so when using a tile size of 32 then there are 
    50x30 pixels if the window has a size of 1600*960. 

    To cull the lights, the scene depth texture is analyzed and the minimum and
    maximum depth per tile is extracted. We could use compute shaders for this task,
    but they are horribly slow. """

    def __init__(self):
        RenderPass.__init__(self)

    def getID(self):
        return "LightCullingPass"

    def setSize(self, sizeX, sizeY):
        """ Sets the amount of tiles. This is usally screenSize/tileSize """
        self.size = LVecBase2i(sizeX, sizeY)

    def setPatchSize(self, patchSizeX, patchSizeY):
        """ Sets the tile size in pixels """
        self.patchSize = LVecBase2i(patchSizeX, patchSizeY)

    def getRequiredInputs(self):
        return {
            "renderedLightsBuffer": "Variables.renderedLightsBuffer",
            "lights": "Variables.allLights",
            "depth": "DeferredScenePass.depth",
            "mainCam": "Variables.mainCam",
            "mainRender": "Variables.mainRender",
            "cameraPosition": "Variables.cameraPosition"
        }

    def create(self):
        self.target = RenderTarget("ComputeLightTileBounds")
        self.target.setSize(self.size.x, self.size.y)
        self.target.addColorTexture()
        self.target.prepareOffscreenBuffer()

        self.target.getColorTexture().setMagfilter(SamplerState.FTNearest)

        self.makePerTileStorage()
        self.target.setShaderInput("destinationBuffer", self.lightPerTileBuffer)

    def makePerTileStorage(self):
        """ Creates the buffer which stores which lights affect which tiles. 
        The first 16 entries are counters which store how many lights of that
        type were rendered, and the following entries store the light indices """
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
        shader = Shader.load(Shader.SLGLSL, 
            "Shader/DefaultPostProcess.vertex",
            "Shader/PrecomputeLights.fragment")
        self.target.setShader(shader)

        return [shader]

    def getOutputs(self):
        return {
            "LightCullingPass.lightsPerTile": lambda: self.lightPerTileBuffer
        }
