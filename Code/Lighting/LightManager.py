
import math
import itertools

from panda3d.core import Vec2, LVecBase2i, Texture, PTAInt

from ..Util.DebugObject import DebugObject
from ..Util.Image import Image

from ..Globals import Globals

from ..Stages.FlagUsedCellsStage import FlagUsedCellsStage
from ..Stages.CollectUsedCellsStage import CollectUsedCellsStage
from ..Stages.CullLightsStage import CullLightsStage
from ..Stages.ApplyLightsStage import ApplyLightsStage
from ..Stages.AmbientStage import AmbientStage
from ..Stages.GBufferStage import GBufferStage
from ..Stages.FinalStage import FinalStage

from ..Interface.GPUCommandQueue import GPUCommandQueue
from ..Interface.GPUCommand import GPUCommand

from Light import Light

class LightManager(DebugObject):

    def __init__(self, pipeline):
        DebugObject.__init__(self, "LightManager")
        self.pipeline = pipeline

        self.lights = [None] * 2**16

        self._computeTileSize()
        self._initLightStorage()
        self._initCommandQueue()
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
        light.setSlot(slot)
        self.lights[slot] = light

        # Create the command and attach it
        commandAdd = GPUCommand(GPUCommand.CMD_STORE_LIGHT)
        light.addToStream(commandAdd)

        # Enforce a width of 4xVec4
        commandAdd.enforceWidth(4 * 4 + 1)
        self.cmdQueue.addCommand(commandAdd)        

        # Now that the light is attached, we can set the dirty flag, because
        # the newest data is now on the gpu
        light.dirty = False

        # Update max light index
        if slot > self.ptaMaxLightIndex[0]:
            self.ptaMaxLightIndex[0] = slot


    def removeLight(self, light):
        """ Removes a light """
        if not light.hasSlot():
            return self.error("Tried to detach light which is not attached!")

        # Todo: Implement me

        self.lights[light.getSlot()] = None
        light.removeSlot()

        # TODO: Udpate max light index!


    def update(self):
        """ Main update method to process the gpu commands """

        # Check for dirty lights
        # dirtyLights = []
        # for i in xrange(self.ptaMaxLightIndex[0] + 1):
        #     light = self.lights[i]
        #     if light and light.dirty:
        #         dirtyLights.append(light)

        # # Process dirty lights
        # for light in dirtyLights:
        #     self.debug("Updating dirty light", light)
                
        #     # TODO: Enqueue update command
        #     light.dirty = False

        self.cmdQueue.processQueue()

    def reloadShaders(self):
        """ Reloads all assigned shaders """
        self.cmdQueue.reloadShaders()

    
    def _initCommandQueue(self):
        self.cmdQueue = GPUCommandQueue(self.pipeline)
        self.cmdQueue.registerInput("LightData", self.imgLightData.tex)

    
    def _initLightStorage(self):
        """ Creates the buffer to store the light data """

        perLightVec4s = 3
        self.imgLightData = Image.create_buffer("LightData", 2**16 * perLightVec4s, Texture.TFloat, Texture.FRgba32)
        self.imgLightData.set_clear_color(0)
        self.imgLightData.clear_image()

        self.ptaMaxLightIndex = PTAInt.emptyArray(1)
        self.ptaMaxLightIndex[0] = 0

        # Register the buffer
        self.pipeline.getStageMgr().add_input("AllLightsData", self.imgLightData.tex)
        self.pipeline.getStageMgr().add_input("maxLightIndex", self.ptaMaxLightIndex)

    
    def _computeTileSize(self):
        """ Computes how many tiles there are on screen """

        self.tileSize = LVecBase2i(self.pipeline.settings.lightGridSizeX, self.pipeline.settings.lightGridSizeY)
        numTilesX = int(math.ceil(Globals.resolution.x / float(self.tileSize.x)))
        numTilesY = int(math.ceil(Globals.resolution.y / float(self.tileSize.y)))
        self.debug("Tile size =",self.tileSize.x,"x",self.tileSize.y, ", Num tiles =",numTilesX,"x",numTilesY)
        self.numTiles = LVecBase2i(numTilesX, numTilesY)

    
    def _initStages(self):
        """ Inits all required stages """
        self.flagCellsStage = FlagUsedCellsStage(self.pipeline)
        self.flagCellsStage.set_tile_amount(self.numTiles)
        self.pipeline.getStageMgr().add_stage(self.flagCellsStage)

        self.collectCellsStage = CollectUsedCellsStage(self.pipeline)
        self.collectCellsStage.set_tile_amount(self.numTiles)
        self.pipeline.getStageMgr().add_stage(self.collectCellsStage)

        self.cullLightsStage = CullLightsStage(self.pipeline)
        self.cullLightsStage.set_tile_amount(self.numTiles)
        self.pipeline.getStageMgr().add_stage(self.cullLightsStage)

        self.applyLightsStage = ApplyLightsStage(self)
        self.pipeline.getStageMgr().add_stage(self.applyLightsStage)

        self.ambientStage = AmbientStage(self)
        self.pipeline.getStageMgr().add_stage(self.ambientStage)

        self.gbufferStage = GBufferStage(self)
        self.pipeline.getStageMgr().add_stage(self.gbufferStage)

        self.finalStage = FinalStage(self)
        self.pipeline.getStageMgr().add_stage(self.finalStage)
