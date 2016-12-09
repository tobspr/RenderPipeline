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

from rpcore.render_stage import RenderStage
from rpcore.image import Image


class CullLightsStage(RenderStage):

    """ This stage takes the list of used cells and creates a list of lights
    for each cell """

    required_pipes = ["CellListBuffer"]
    required_inputs = ["AllLightsData", "maxLightIndex"]

    def __init__(self, pipeline):
        RenderStage.__init__(self, pipeline)
        self.max_lights_per_cell = pipeline.settings["lighting.max_lights_per_cell"]

        if self.max_lights_per_cell > 2**16:
            self.fatal("lighting.max_lights_per_cell must be <=", 2**16, "!")

        self.slice_width = pipeline.settings["lighting.culling_slice_width"]
        self.culling_grid_slices = pipeline.settings["lighting.culling_grid_slices"]
        self.cull_threads = 32

        # Amount of light classes. Has to match the ones in LightClassification.inc.glsl
        self.num_light_classes = 4

    @property
    def produced_pipes(self):
        return {
            "PerCellLights": self.grouped_cell_lights,
            "PerCellLightsCounts": self.grouped_cell_lights_counts
        }

    @property
    def produced_defines(self):
        return {
            "LC_SLICE_WIDTH": self.slice_width,
            "LC_CULL_THREADS": self.cull_threads,
            "LC_LIGHT_CLASS_COUNT": self.num_light_classes
        }

    def create(self):

        # Create all required buffers
        self.frustum_lights_ctr = Image.create_counter("VisibleLightCount")
        self.frustum_lights = Image.create_buffer("FrustumLights", self._pipeline.light_mgr.MAX_LIGHTS, "R16UI")
        
        self.per_slice_lights = Image.create_buffer("PerSliceLights", self.culling_grid_slices * self._pipeline.light_mgr.MAX_LIGHTS, "R16UI")
        self.per_slice_lights_ctr = Image.create_buffer("PerSliceLightsCounter", self.culling_grid_slices, "R32I")

        self.per_cell_lights = Image.create_buffer("PerCellLights", 0, "R16UI")
        self.per_cell_light_counts = Image.create_buffer("PerCellLightCounts", 0, "R32I") # Needs to be R32 for atomic add in cull stage
        
        self.grouped_cell_lights = Image.create_buffer("GroupedPerCellLights", 0, "R16UI")
        self.grouped_cell_lights_counts = Image.create_buffer("GroupedPerCellLightsCount", 0, "R16UI")

        # Target to take the list of all lights, and output a list of all lights
        # in the current camera frustum
        # TODO: Use no oversized triangle in this stage
        self.target_visible = self.create_target("ViewFrustumCull")
        self.target_visible.size = 16, 16
        self.target_visible.prepare_buffer()
        self.target_visible.set_shader_input("FrustumLights", self.frustum_lights)
        self.target_visible.set_shader_input("FrustumLightsCount", self.frustum_lights_ctr)

        # Target which takes the frustum lights and outputs a list of intersected lights
        # for each slice of the culling frustum
        # TODO: Use no oversized triangle in this stage
        self.target_cull_slices = self.create_target("PreCullSlices")
        self.target_cull_slices.size = self.culling_grid_slices, 128
        self.target_cull_slices.prepare_buffer()
        self.target_cull_slices.set_shader_input("FrustumLights", self.frustum_lights)
        self.target_cull_slices.set_shader_input("FrustumLightsCount", self.frustum_lights_ctr)
        self.target_cull_slices.set_shader_input("PerSliceLights", self.per_slice_lights)
        self.target_cull_slices.set_shader_input("PerSliceLightsCount", self.per_slice_lights_ctr)

        # Target which takes the per-slice culled lights, and produces the list of visible
        # lights for each voxel in our clustered frustum
        # TODO: Use no oversized triangle in this stage
        self.target_cull = self.create_target("CullLights")
        self.target_cull.size = 0, 0
        self.target_cull.prepare_buffer()
        self.target_cull.set_shader_input("PerCellLightsBuffer", self.per_cell_lights)
        self.target_cull.set_shader_input("PerCellLightCountsBuffer", self.per_cell_light_counts)
        self.target_cull.set_shader_input("PerSliceLights", self.per_slice_lights)
        self.target_cull.set_shader_input("PerSliceLightsCount", self.per_slice_lights_ctr)
        self.target_cull.set_shader_input("threadCount", self.cull_threads)
        
        # Target which takes the per-voxel light list and sorts it by light type, to
        # get better branching coherency
        # TODO: Use no oversized triangle in this stage
        self.target_group = self.create_target("GroupLightsByClass")
        self.target_group.size = 0, 0
        self.target_group.prepare_buffer()
        self.target_group.set_shader_input("PerCellLightsBuffer", self.per_cell_lights)
        self.target_group.set_shader_input("PerCellLightCountsBuffer", self.per_cell_light_counts)
        self.target_group.set_shader_input("GroupedCellLightsBuffer", self.grouped_cell_lights)
        self.target_group.set_shader_input("GroupedPerCellLightsCountBuffer", self.grouped_cell_lights_counts)
        self.target_group.set_shader_input("threadCount", 1)

    def update(self):
        self.frustum_lights_ctr.clear_image()
        self.per_slice_lights_ctr.clear_image()

    def set_dimensions(self):
        # Updates the dimensions of all textures / buffers which depend on the screen size

        max_cells = self._pipeline.light_mgr.total_tiles

        num_rows_threaded = int(
            math.ceil((max_cells * self.cull_threads) / float(self.slice_width)))
        num_rows = int(math.ceil(max_cells / float(self.slice_width)))

        # Update the size of the buffer which keeps the per-cell lights, since the cell count might have changed
        self.per_cell_lights.set_x_size(max_cells * self.max_lights_per_cell)
        self.per_cell_light_counts.set_x_size(max_cells)

        self.grouped_cell_lights.set_x_size(
            max_cells * (self.max_lights_per_cell + self.num_light_classes))
        self.grouped_cell_lights_counts.set_x_size(max_cells * (1 + self.num_light_classes))

        self.target_cull.size = self.slice_width, num_rows_threaded
        self.target_group.size = self.slice_width, num_rows

    def reload_shaders(self):
        self.target_cull.shader = self.load_shader("tiled_culling.vert.glsl", "cull_lights.frag.glsl")
        self.target_group.shader = self.load_shader("tiled_culling.vert.glsl", "group_lights.frag.glsl")
        self.target_visible.shader = self.load_shader("view_frustum_cull.frag.glsl")
        self.target_cull_slices.shader = self.load_shader("pre_cull_slices.frag.glsl")
