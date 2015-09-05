
import math
import itertools

from panda3d.core import Vec2, LVecBase2i, Texture, PTAInt

from ..Util.DebugObject import DebugObject
from ..Util.Image import Image
from ..Util.FunctionDecorators import protected

from ..Globals import Globals

from ..Stages.FlagUsedCellsStage import FlagUsedCellsStage
from ..Stages.CollectUsedCellsStage import CollectUsedCellsStage
from ..Stages.CullLightsStage import CullLightsStage

from Light import Light

class LightManager(DebugObject):

    def __init__(self, pipeline):
        DebugObject.__init__(self, "LightManager")
        self.pipeline = pipeline

        self.lights = [None] * 2**16

        self._computeTileSize()
        self._initLightStorage()
        self._initStages()

    def initDefines(self):
        """ Inits the common defines """
        define = self.pipeline.getStageMgr().define

        settings = self.pipeline.settings

        define("LC_TILE_SIZE_X", settings.lightGridSizeX)
        define("LC_TILE_SIZE_Y", settings.lightGridSizeY)
        define("LC_TILE_AMOUNT_X", self.numTiles.x)
        define("LC_TILE_AMOUNT_Y", self.numTiles.y)
        define("LC_TILE_SLICES", settings.lightGridSlices)

    def addLight(self, light):
        """ Adds a new light """

        assert(isinstance(light, Light))

        # Find the first free slot
        slot = next((i for i, x in enumerate(self.lights) if x is None), None)

        if slot is None:
            return self.error("Light limit of", 2**16, "reached!")

        # Store slot in light, so we can access it later
        light.__slot = slot

        self._updateMaxLightIndex()


    def removeLight(self, light):
        """ Removes a light """
        if not hasattr(light, "__slot"):
            return self.error("Tried to detach light which is not attached!")

        # Todo: Implement me

        self.lights[light.__slot] = None
        del light.__slot

        self._updateMaxLightIndex()

    @protected
    def _updateMaxLightIndex(self):
        """ Checks for the last light index """
        try:
            maxIdx = next(i for i,v in itertools.izip(xrange(len(self.lights)-1, 0, -1), reversed(self.lights)) if v is not None)
        except StopIteration: 
            maxIdx = 0
        self.debug("Max light index is", maxIdx)
        self.ptaMaxLightIndex[0] = maxIdx

    @protected
    def _initLightStorage(self):
        """ Creates the buffer to store the light data """

        perLightVec4s = 3
        self.imgLightData = Image.createBuffer("LightData", 2**16 * perLightVec4s, Texture.FRgba32, Texture.TFloat)
        self.imgLightData.setClearColor(0)
        self.imgLightData.clearImage()

        self.ptaMaxLightIndex = PTAInt.emptyArray(1)
        self.ptaMaxLightIndex[0] = 0

        # Register the buffer
        self.pipeline.getStageMgr().addInput("AllLightsData", self.imgLightData)
        self.pipeline.getStageMgr().addInput("MaxLightIndex", self.ptaMaxLightIndex)

    @protected
    def _computeTileSize(self):
        """ Computes how many tiles there are on screen """

        self.tileSize = LVecBase2i(self.pipeline.settings.lightGridSizeX, self.pipeline.settings.lightGridSizeY)
        numTilesX = int(math.ceil(Globals.resolution.x / float(self.tileSize.x)))
        numTilesY = int(math.ceil(Globals.resolution.y / float(self.tileSize.y)))
        self.debug("Tile size =",self.tileSize.x,"x",self.tileSize.y, ", Num tiles =",numTilesX,"x",numTilesY)
        self.numTiles = LVecBase2i(numTilesX, numTilesY)

    @protected
    def _initStages(self):
        """ Inits all required stages """
        self.flagCellsStage = FlagUsedCellsStage(self.pipeline)
        self.flagCellsStage.setTileAmount(self.numTiles)
        self.pipeline.getStageMgr().addStage(self.flagCellsStage)

        self.collectCellsStage = CollectUsedCellsStage(self.pipeline)
        self.collectCellsStage.setTileAmount(self.numTiles)
        self.pipeline.getStageMgr().addStage(self.collectCellsStage)

        self.cullLightsStage = CullLightsStage(self.pipeline)
        self.cullLightsStage.setTileAmount(self.numTiles)
        self.pipeline.getStageMgr().addStage(self.cullLightsStage)
        
