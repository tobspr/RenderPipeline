"""

RenderPipeline

Copyright (c) 2014-2015 tobspr <tobias.springer1@gmail.com>

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

from ..RenderStage import RenderStage
from ..Util.Image import Image


class FlagUsedCellsStage(RenderStage):

    """ This stage flags all used cells based on the depth buffer """

    required_pipes = ["GBuffer"]
    required_inputs = []

    def __init__(self, pipeline):
        RenderStage.__init__(self, "FlagUsedCellsStage", pipeline)
        self._tile_amount = None

    def set_tile_amount(self, tile_amount):
        """ Sets the cell tile size """
        self._tile_amount = tile_amount

    def get_produced_pipes(self):
        return {"FlaggedCells": self._cell_grid_flags}

    def create(self):
        self._target = self._create_target("FlagUsedCells")
        self._target.prepare_offscreen_buffer()

        self._cell_grid_flags = Image.create_2d_array(
            "CellGridFlags", self._tile_amount.x, self._tile_amount.y,
            self._pipeline.get_setting("lighting.culling_grid_slices"),
            Texture.T_unsigned_byte, Texture.F_red)
        self._cell_grid_flags.set_clear_color(0)

        self._target.set_shader_input("cellGridFlags", self._cell_grid_flags)

    def update(self):
        self._cell_grid_flags.clear_image()

    def set_shaders(self):
        self._target.set_shader(self._load_shader("Stages/FlagUsedCells.frag"))
