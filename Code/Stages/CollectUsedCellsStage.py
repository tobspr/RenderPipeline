
from panda3d.core import Texture

from ..RenderStage import RenderStage
from ..Util.Image import Image


class CollectUsedCellsStage(RenderStage):

    """ This stage collects the flagged cells from the FlagUsedCellsStage and
    makes a list of them """

    required_pipes = ["FlaggedCells"]

    def __init__(self, pipeline):
        RenderStage.__init__(self, "CollectUsedCellsStage", pipeline)
        self._tile_amount = None

    def set_tile_amount(self, tile_amount):
        """ Sets the cell tile size """
        self._tile_amount = tile_amount

    def get_produced_pipes(self):
        return {
            "CellListBuffer": self._cell_list_buffer.get_texture(),
            "CellIndices": self._cell_index_buffer.get_texture(),
        }

    def create(self):
        self._target = self._create_target("CollectUsedCells")
        self._target.set_size(self._tile_amount.x, self._tile_amount.y)
        self._target.prepare_offscreen_buffer()

        num_slices = self._pipeline.get_settings().LightGridSlices
        max_cells = self._tile_amount.x * self._tile_amount.y * num_slices

        self.debug("Allocating", max_cells, "cells")
        self._cell_list_buffer = Image.create_buffer(
            "CellList", max_cells, Texture.T_int, Texture.F_r32i)
        self._cell_list_buffer.set_clear_color(0)
        self._cell_index_buffer = Image.create_2d_array(
            "CellIndices", self._tile_amount.x, self._tile_amount.y,
            num_slices, Texture.T_int, Texture.F_r32i)
        self._cell_index_buffer.set_clear_color(0)

        self._target.set_shader_input(
            "cellListBuffer", self._cell_list_buffer.get_texture())
        self._target.set_shader_input(
            "cellListIndices", self._cell_index_buffer.get_texture())

    def update(self):
        self._cell_list_buffer.clear_image()
        self._cell_index_buffer.clear_image()

    def set_shaders(self):
        self._target.set_shader(
            self._load_shader("Stages/CollectUsedCells.frag"))

    def resize(self):
        RenderStage.resize(self)
        self.debug("Resizing pass")

    def cleanup(self):
        RenderStage.cleanup(self)
        self.debug("Cleanup pass")
