
import math

from panda3d.core import LVecBase2i, Texture, PTAInt

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

from .Light import Light


class LightManager(DebugObject):

    """ This class manages all the lights """

    _MAX_LIGHTS = 2 ** 16

    def __init__(self, pipeline):
        """ Constructs the light manager """
        DebugObject.__init__(self, "LightManager")
        self._pipeline = pipeline

        self._lights = [None] * self._MAX_LIGHTS

        self._compute_tile_size()
        self._init_light_storage()
        self._init_command_queue()
        self._init_stages()

    def init_defines(self):
        """ Inits the common defines """
        define = self._pipeline.get_stage_mgr().define
        settings = self._pipeline.get_settings()

        define("LC_TILE_SIZE_X", settings.LightGridSizeX)
        define("LC_TILE_SIZE_Y", settings.LightGridSizeY)
        define("LC_TILE_AMOUNT_X", self._num_tiles.x)
        define("LC_TILE_AMOUNT_Y", self._num_tiles.y)
        define("LC_TILE_SLICES", settings.LightGridSlices)

    def add_light(self, light):
        """ Adds a new light """

        assert(isinstance(light, Light))

        # Find the first free slot
        slot = next((i for i, x in enumerate(self._lights) if x is None), None)

        if slot is None:
            return self.error("Light limit of", 2**16, "reached!")

        # Store slot in light, so we can access it later
        light.set_slot(slot)
        self._lights[slot] = light

        # Create the command and attach it
        command_add = GPUCommand(GPUCommand.CMD_STORE_LIGHT)
        light.add_to_stream(command_add)

        # Enforce a width of 4xVec4
        command_add.enforce_width(4 * 4 + 1)
        self._cmd_queue.add_command(command_add)        

        # Now that the light is attached, we can set the dirty flag, because
        # the newest data is now on the gpu
        light._unset_dirty()

        # Update max light index
        if slot > self._pta_max_light_index[0]:
            self._pta_max_light_index[0] = slot

    def remove_light(self, light):
        """ Removes a light """
        if not light.has_slot():
            return self.error("Tried to detach light which is not attached!")

        # Todo: Implement me

        self._lights[light.get_slot()] = None
        light.remove_slot()

        # TODO: Udpate max light index!
        raise NotImplementedError()

    def update(self):
        """ Main update method to process the gpu commands """

        # Check for dirty lights
        # dirtyLights = []
        # for i in xrange(self._pta_max_light_index[0] + 1):
        #     light = self._lights[i]
        #     if light and light.dirty:
        #         dirtyLights.append(light)

        # # Process dirty lights
        # for light in dirtyLights:
        #     self.debug("Updating dirty light", light)
        #     # TODO: Enqueue update command
        #     light.dirty = False
        self._cmd_queue.process_queue()

    def reload_shaders(self):
        """ Reloads all assigned shaders """
        self._cmd_queue.reload_shaders()

    def _init_command_queue(self):
        self._cmd_queue = GPUCommandQueue(self._pipeline)
        self._cmd_queue.register_input(
            "LightData", self._img_light_data.get_texture())

    def _init_light_storage(self):
        """ Creates the buffer to store the light data """

        per_light_vec4s = 3
        self._img_light_data = Image.create_buffer(
            "LightData", self._MAX_LIGHTS * per_light_vec4s, Texture.T_float,
            Texture.F_rgba32)
        self._img_light_data.set_clear_color(0)
        self._img_light_data.clear_image()

        self._pta_max_light_index = PTAInt.empty_array(1)
        self._pta_max_light_index[0] = 0

        # Register the buffer
        self._pipeline.get_stage_mgr().add_input("AllLightsData", self._img_light_data.get_texture())
        self._pipeline.get_stage_mgr().add_input("maxLightIndex", self._pta_max_light_index)

    def _compute_tile_size(self):
        """ Computes how many tiles there are on screen """

        self._tile_size = LVecBase2i(
            self._pipeline.get_settings().LightGridSizeX,
            self._pipeline.get_settings().LightGridSizeY)
        num_tiles_x = int(math.ceil(Globals.resolution.x /
                                    float(self._tile_size.x)))
        num_tiles_y = int(math.ceil(Globals.resolution.y /
                                    float(self._tile_size.y)))
        self.debug("Tile size =", self._tile_size.x, "x", self._tile_size.y,
                   ", Num tiles =", num_tiles_x, "x", num_tiles_y)
        self._num_tiles = LVecBase2i(num_tiles_x, num_tiles_y)

    def _init_stages(self):
        """ Inits all required stages """
        self._flag_cells_stage = FlagUsedCellsStage(self._pipeline)
        self._flag_cells_stage.set_tile_amount(self._num_tiles)
        self._pipeline.get_stage_mgr().add_stage(self._flag_cells_stage)

        self._collect_cells_stage = CollectUsedCellsStage(self._pipeline)
        self._collect_cells_stage.set_tile_amount(self._num_tiles)
        self._pipeline.get_stage_mgr().add_stage(self._collect_cells_stage)

        self._cull_lights_stage = CullLightsStage(self._pipeline)
        self._cull_lights_stage.set_tile_amount(self._num_tiles)
        self._pipeline.get_stage_mgr().add_stage(self._cull_lights_stage)

        self._apply_lights_stage = ApplyLightsStage(self)
        self._pipeline.get_stage_mgr().add_stage(self._apply_lights_stage)

        self._ambient_stage = AmbientStage(self)
        self._pipeline.get_stage_mgr().add_stage(self._ambient_stage)

        self._gbuffer_stage = GBufferStage(self)
        self._pipeline.get_stage_mgr().add_stage(self._gbuffer_stage)

        self._final_stage = FinalStage(self)
        self._pipeline.get_stage_mgr().add_stage(self._final_stage)
