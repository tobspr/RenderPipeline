
import math

from panda3d.core import Vec2, LVecBase2i

from ..Util.DebugObject import DebugObject
from ..Util.Image import Image
from ..Util.FunctionDecorators import protected

from ..Globals import Globals

from ..Stages.FlagUsedCellsStage import FlagUsedCellsStage
from ..Stages.CollectUsedCellsStage import CollectUsedCellsStage
from ..Stages.CullLightsStage import CullLightsStage

class LightManager(DebugObject):

    def __init__(self, pipeline):
        DebugObject.__init__(self, "LightManager")
        self.pipeline = pipeline

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

    @protected
    def _initLightStorage(self):
        """ """

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
        
