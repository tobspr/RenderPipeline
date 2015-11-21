
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
from ..Stages.DownscaleZStage import DownscaleZStage

from ..GPUCommandQueue import GPUCommandQueue
from ..Native import GPUCommand, Light, LightStorage


class LightManager(DebugObject):

    """ This class manages all the lights """

    _MAX_LIGHTS = 2 ** 16

    def __init__(self, pipeline):
        """ Constructs the light manager """
        DebugObject.__init__(self, "LightManager")
        self._pipeline = pipeline
        self._light_storage = LightStorage()

        self._compute_tile_size()
        self._init_light_storage()
        self._init_command_queue()
        self._init_stages()

    def init_defines(self):
        """ Inits the common defines """
        define = self._pipeline.get_stage_mgr().define

        define("LC_TILE_SIZE_X", self._pipeline.get_setting("lighting.culling_grid_size_x"))
        define("LC_TILE_SIZE_Y", self._pipeline.get_setting("lighting.culling_grid_size_y"))
        define("LC_TILE_AMOUNT_X", self._num_tiles.x)
        define("LC_TILE_AMOUNT_Y", self._num_tiles.y)
        define("LC_TILE_SLICES", self._pipeline.get_setting("lighting.culling_grid_slices"))
        define("LC_MAX_DISTANCE", self._pipeline.get_setting("lighting.culling_max_distance"))

    def add_light(self, light):
        """ Adds a new light """
        self._light_storage.add_light(light)
        self._pta_max_light_index[0] = self._light_storage.get_max_light_index();

    def remove_light(self, light):
        """ Removes a light """
        if not light.has_slot():
            return self.error("Tried to detach light which is not attached!")

        self._light_storage.remove_light(light)

    def update(self):
        """ Main update method to process the gpu commands """
        self._light_storage.update()
        self._cmd_queue.process_queue()

    def reload_shaders(self):
        """ Reloads all assigned shaders """
        self._cmd_queue.reload_shaders()

    def _init_command_queue(self):
        self._cmd_queue = GPUCommandQueue(self._pipeline)
        self._cmd_queue.register_input(
            "LightData", self._img_light_data.get_texture())
        self._light_storage.set_command_list(self._cmd_queue.get_cmd_list())

    def _init_light_storage(self):
        """ Creates the buffer to store the light data """

        per_light_vec4s = 4
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
            self._pipeline.get_setting("lighting.culling_grid_size_x"),
            self._pipeline.get_setting("lighting.culling_grid_size_x"))
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

        self._apply_lights_stage = ApplyLightsStage(self._pipeline)
        self._pipeline.get_stage_mgr().add_stage(self._apply_lights_stage)

        self._ambient_stage = AmbientStage(self._pipeline)
        self._pipeline.get_stage_mgr().add_stage(self._ambient_stage)

        self._gbuffer_stage = GBufferStage(self._pipeline)
        self._pipeline.get_stage_mgr().add_stage(self._gbuffer_stage)

        self._final_stage = FinalStage(self._pipeline)
        self._pipeline.get_stage_mgr().add_stage(self._final_stage)

        self._downscale_z_stage = DownscaleZStage(self._pipeline)
        self._pipeline.get_stage_mgr().add_stage(self._downscale_z_stage)
