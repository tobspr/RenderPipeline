"""

RenderPipeline

Copyright (c) 2014-2016 tobspr <tobias.springer1@gmail.com>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
 	 	    	 	
"""

import math

from panda3d.core import LVecBase2i, Texture, PTAInt

from ..Util.DebugObject import DebugObject
from ..Util.Image import Image

from ..Globals import Globals

from ..Stages.FlagUsedCellsStage import FlagUsedCellsStage
from ..Stages.CollectUsedCellsStage import CollectUsedCellsStage
from ..Stages.CullLightsStage import CullLightsStage
from ..Stages.ApplyLightsStage import ApplyLightsStage
from ..Stages.ShadowStage import ShadowStage

from ..GPUCommandQueue import GPUCommandQueue
from ..Native import InternalLightManager, PointLight, ShadowManager
from ..BaseManager import BaseManager

class LightManager(BaseManager):

    """ This class is a wrapper around the InternalLightManager, and provides
    additional functionality like setting up all required stages and defines."""

    _MAX_LIGHTS = 65535
    _MAX_SOURCES = 2048

    def __init__(self, pipeline):
        """ Constructs the light manager """
        BaseManager.__init__(self)
        self._pipeline = pipeline
        self._compute_tile_size()
        self._init_internal_mgr()
        self._init_command_queue()
        self._init_shadow_manager()
        self._init_stages()

    def init_defines(self):
        """ Inits the common defines """
        define = self._pipeline.stage_mgr.define

        define("LC_TILE_SIZE_X", self._tile_size.x)
        define("LC_TILE_SIZE_Y", self._tile_size.y)
        define("LC_TILE_AMOUNT_X", self._num_tiles.x)
        define("LC_TILE_AMOUNT_Y", self._num_tiles.y)
        define("LC_TILE_SLICES", self._pipeline.get_setting("lighting.culling_grid_slices"))
        define("LC_MAX_DISTANCE", self._pipeline.get_setting("lighting.culling_max_distance"))
        define("LC_CULLING_SLICE_WIDTH", self._pipeline.get_setting("lighting.culling_slice_width"))

        define("SHADOW_ATLAS_SIZE", self._pipeline.get_setting("shadows.atlas_size"))

        # Register all light types as defines
        for attr in dir(PointLight):
            if attr.startswith("LT_"):
                attr_value = getattr(PointLight, attr)
                define(attr.upper(), attr_value)

    def add_light(self, light):
        """ Adds a new light """
        self._internal_mgr.add_light(light)
        self._pta_max_light_index[0] = self._internal_mgr.get_max_light_index()

    def remove_light(self, light):
        """ Removes a light """
        self._internal_mgr.remove_light(light)
        self._pta_max_light_index[0] = self._internal_mgr.get_max_light_index()

    def get_num_lights(self):
        """ Returns the amount of stored lights """
        return self._internal_mgr.get_num_lights()

    def get_num_shadow_sources(self):
        """ Returns the amount of stored shadow sources """
        return self._internal_mgr.get_num_shadow_sources()

    def get_cmd_queue(self):
        """ Returns a handle to the GPU Command Queue """
        return self._cmd_queue

    def do_update(self):
        """ Main update method to process the GPU commands """
        self._internal_mgr.update()
        self._shadow_manager.update()
        self._cmd_queue.process_queue()

    def reload_shaders(self):
        """ Reloads all assigned shaders """
        self._cmd_queue.reload_shaders()

    def _init_command_queue(self):
        """ Inits the command queue """
        self._cmd_queue = GPUCommandQueue(self._pipeline)
        self._cmd_queue.register_input("LightData", self._img_light_data)
        self._cmd_queue.register_input("SourceData", self._img_source_data)

        # Register the command list
        self._internal_mgr.set_command_list(self._cmd_queue.command_list)

    def _init_shadow_manager(self):
        """ Inits the shadow manager """
        self._shadow_manager = ShadowManager()
        self._shadow_manager.set_max_updates(self._pipeline.get_setting("shadows.max_updates"))
        self._shadow_manager.set_atlas_size(self._pipeline.get_setting("shadows.atlas_size"))
        self._shadow_manager.set_scene(Globals.base.render)
        self._shadow_manager.set_tag_state_manager(self._pipeline.tag_mgr)

        # Register the shadow manager
        self._internal_mgr.set_shadow_manager(self._shadow_manager)

    def init_shadows(self):
        """ Inits the shadows, this needs to get called after the stages were
        created, because we need the GraphicsOutput of the shadow atlas, which
        is not available earlier """
        self._shadow_manager.set_atlas_graphics_output(self._shadow_stage._target.get_internal_buffer())
        self._shadow_manager.init()

    def _init_internal_mgr(self):
        """ Creates the light storage manager and the buffer to store the light data """
        self._internal_mgr = InternalLightManager()

        # Storage for the Lights
        per_light_vec4s = 4
        self._img_light_data = Image.create_buffer(
            "LightData", self._MAX_LIGHTS * per_light_vec4s, Texture.T_float,
            Texture.F_rgba16)
        self._img_light_data.set_clear_color(0)
        self._img_light_data.clear_image()

        self._pta_max_light_index = PTAInt.empty_array(1)
        self._pta_max_light_index[0] = 0

        # Storage for the shadow sources
        per_source_vec4s = 5
        self._img_source_data = Image.create_buffer(
            "ShadowSourceData", self._MAX_SOURCES * per_source_vec4s, Texture.T_float,
            Texture.F_rgba16)
        self._img_light_data.set_clear_color(0)
        self._img_light_data.clear_image()

        # Register the buffer
        add_input = self._pipeline.stage_mgr.add_input
        add_input("AllLightsData", self._img_light_data)
        add_input("ShadowSourceData", self._img_source_data)
        add_input("maxLightIndex", self._pta_max_light_index)

    def _compute_tile_size(self):
        """ Computes how many tiles there are on screen """
        self._tile_size = LVecBase2i(
            self._pipeline.get_setting("lighting.culling_grid_size_x"),
            self._pipeline.get_setting("lighting.culling_grid_size_y"))
        num_tiles_x = int(math.ceil(Globals.resolution.x /
                                    float(self._tile_size.x)))
        num_tiles_y = int(math.ceil(Globals.resolution.y /
                                    float(self._tile_size.y)))
        self.debug("Tile size =", self._tile_size.x, "x", self._tile_size.y,
                   ", Num tiles =", num_tiles_x, "x", num_tiles_y)
        self._num_tiles = LVecBase2i(num_tiles_x, num_tiles_y)

    def _init_stages(self):
        """ Inits all required stages for the lighting """

        add_stage = self._pipeline.stage_mgr.add_stage

        self._flag_cells_stage = FlagUsedCellsStage(self._pipeline)
        self._flag_cells_stage.set_tile_amount(self._num_tiles)
        add_stage(self._flag_cells_stage)

        self._collect_cells_stage = CollectUsedCellsStage(self._pipeline)
        self._collect_cells_stage.set_tile_amount(self._num_tiles)
        add_stage(self._collect_cells_stage)

        self._cull_lights_stage = CullLightsStage(self._pipeline)
        self._cull_lights_stage.set_tile_amount(self._num_tiles)
        add_stage(self._cull_lights_stage)

        self._apply_lights_stage = ApplyLightsStage(self._pipeline)
        add_stage(self._apply_lights_stage)

        self._shadow_stage = ShadowStage(self._pipeline)
        self._shadow_stage.size = self._shadow_manager.get_atlas_size()
        add_stage(self._shadow_stage)
