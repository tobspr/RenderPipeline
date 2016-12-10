/**
 *
 * RenderPipeline
 *
 * Copyright (c) 2014-2016 tobspr <tobias.springer1@gmail.com>
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 * THE SOFTWARE.
 *
 */

#version 430

// This shader collects the list of all lights for a given cell, sorts them
// and then writes them out as a list.

layout(early_fragment_tests) in;

#pragma include "render_pipeline_base.inc.glsl"
#pragma include "includes/transforms.inc.glsl"
#pragma include "includes/light_culling.inc.glsl"
#pragma include "includes/light_data.inc.glsl"
#pragma include "includes/light_classification.inc.glsl"

uniform isamplerBuffer CellListBuffer;
uniform usamplerBuffer PerSliceLights;
uniform isamplerBuffer PerSliceLightsCount;

uniform writeonly uimageBuffer PerCellLightsBuffer;
layout(r32i) uniform iimageBuffer PerCellLightCountsBuffer;

uniform samplerBuffer AllLightsData;

void main() {

    ivec2 coord = ivec2(gl_FragCoord.xy);

    int thread_id = coord.x + coord.y * LC_CULLING_SLICE_WIDTH;
    int local_offset = thread_id % LC_CULL_THREADS;

    // Find the index of the cell we are about to process
    // Add one since the first pixel is the count of visible cells
    int idx = 1 + thread_id / LC_CULL_THREADS; 
    int num_total_cells = texelFetch(CellListBuffer, 0).x;
    ivec2 tile_size = ivec2(LC_TILE_SIZE_X, LC_TILE_SIZE_Y);

    // If we found no remaining cell, we are done, so just return and hope for
    // good coherency.
    if (idx > num_total_cells) {
        return;
    }

    // Fetch the cell data, this contains the cells position
    int packed_cell_data = texelFetch(CellListBuffer, idx).x;
    int cell_x, cell_y, cell_slice;
    unpack_cell_data(packed_cell_data, cell_x, cell_y, cell_slice);

    // Find the tiles minimum and mapximum distance
    float min_distance = get_distance_from_slice(cell_slice);
    float max_distance = get_distance_from_slice(cell_slice + 1);

    // Get the offset in the per-cell light list
    int storage_offs = LC_MAX_LIGHTS_PER_CELL * idx;

    // Get amount of visible lights in slice
    int max_slice_lights = texelFetch(PerSliceLightsCount, cell_slice).x;

    // Offset of the per-slice data, stored in a buffer texture instead of
    // texture2D due to a panda bug.
    int slice_offs = cell_slice * LC_MAX_LIGHTS;

    Frustum view_frustum = make_view_frustum(
        cell_x, cell_y, tile_size, min_distance, max_distance);

    // Cull all lights
    for (int i = local_offset; i < max_slice_lights; i += LC_CULL_THREADS) {
        int light_index = int(texelFetch(PerSliceLights, slice_offs + i).x);

        // Fetch data of current light
        LightData light_data = read_light_data(AllLightsData, light_index);
        bool visible = cull_light(light_data, view_frustum);

        // Uncomment this to see if the culling produces any issues
        visible = true; // XXX

        // Write the light to the light buffer
        if (visible) {
            int num_rendered_lights = imageAtomicAdd(PerCellLightCountsBuffer, idx, 1).x;

            // When we reached the maximum amount of lights for this tile, stop.
            // At this point, its actually too late, because another thread might
            // have written over the bounds already, but we try to prevent further errors.
            if (num_rendered_lights >= LC_MAX_LIGHTS_PER_CELL) {
                break;
            }

            imageStore(PerCellLightsBuffer, storage_offs + num_rendered_lights, uvec4(light_index));
        }
    }
}
