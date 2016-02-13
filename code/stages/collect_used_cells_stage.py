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

from panda3d.core import Texture

from ..render_stage import RenderStage
from ..util.image import Image

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

    @property
    def produced_pipes(self):
        return {
            "CellListBuffer": self._cell_list_buffer,
            "CellIndices": self._cell_index_buffer,
        }

    def create(self):
        self._target = self.make_target("CollectUsedCells")
        self._target.size = self._tile_amount.x, self._tile_amount.y
        self._target.prepare_offscreen_buffer()

        num_slices = self._pipeline.get_setting("lighting.culling_grid_slices")
        max_cells = self._tile_amount.x * self._tile_amount.y * num_slices

        self.debug("Allocating", max_cells, "cells")
        self._cell_list_buffer = Image.create_buffer(
            "CellList", max_cells, Texture.T_int, Texture.F_r32i)
        self._cell_list_buffer.set_clear_color(0)
        self._cell_index_buffer = Image.create_2d_array(
            "CellIndices", self._tile_amount.x, self._tile_amount.y,
            num_slices, Texture.T_int, Texture.F_r32i)
        self._cell_index_buffer.set_clear_color(0)

        self._target.set_shader_input("cellListBuffer", self._cell_list_buffer)
        self._target.set_shader_input("cellListIndices", self._cell_index_buffer)

    def update(self):
        self._cell_list_buffer.clear_image()
        self._cell_index_buffer.clear_image()

    def set_shaders(self):
        self._target.set_shader(
            self.load_shader("stages/collect_used_cells.frag.glsl"))
