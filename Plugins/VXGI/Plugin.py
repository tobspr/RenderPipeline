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
# Load the plugin api
from .. import *

from .VoxelizationStage import VoxelizationStage

class Plugin(BasePlugin):

    @PluginHook("on_stage_setup")
    def setup_stages(self):
        self._voxel_stage = self.create_stage(VoxelizationStage)

    @PluginHook("pre_render_update")
    def update(self):
        self._queue.exec_next_task()

    @PluginHook("on_pipeline_created")
    def on_created(self):
        self._queue = RepeatedTaskQueue()
        self._queue.add(self._voxelize_x, self._voxelize_y, self._voxelize_z)
        self._queue.add(self._generate_mipmaps)

    def _set_grid_pos(self):
        """ Finds the new grid position """
        grid_pos = Globals.base.camera.get_pos(Globals.base.render)
        self._voxel_stage.set_grid_position(grid_pos)

    def _voxelize_x(self):
        self._set_grid_pos()
        self._voxel_stage.set_state(VoxelizationStage.S_voxelize_x)

    def _voxelize_y(self):
        self._voxel_stage.set_state(VoxelizationStage.S_voxelize_y)

    def _voxelize_z(self):
        self._voxel_stage.set_state(VoxelizationStage.S_voxelize_z)

    def _generate_mipmaps(self):
        self._voxel_stage.set_state(VoxelizationStage.S_gen_mipmaps)
