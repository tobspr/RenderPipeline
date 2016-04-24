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

#pragma include "render_pipeline_base.inc.glsl"
#pragma include "includes/transforms.inc.glsl"
#pragma include "includes/light_culling.inc.glsl"
#pragma include "includes/light_data.inc.glsl"
#pragma include "includes/light_classification.inc.glsl"

uniform isamplerBuffer CellListBuffer;
uniform isamplerBuffer FrustumLights;
uniform writeonly iimageBuffer RESTRICT PerCellLightsBuffer;

uniform samplerBuffer AllLightsData;

void main() {

    ivec2 coord = ivec2(gl_FragCoord.xy);

    // Find the index of the cell we are about to process
    int idx = 1 + coord.x + coord.y * LC_CULLING_SLICE_WIDTH;
    int num_total_cells = texelFetch(CellListBuffer, 0).x;
    ivec2 precompute_size = MainSceneData.lc_tile_count;

    // If we found no remaining cell, we are done, so just return and hope for
    // good coherency.
    if (idx > num_total_cells) {
        return;
    }

    // Fetch the cell data, this contains the cells position
    int packed_cell_data = texelFetch(CellListBuffer, idx).x;
    int cell_x, cell_y, cell_slice;
    unpack_cell_data(packed_cell_data, cell_x, cell_y, cell_slice);

    // Amount to increment the minimum and maximum distance of the slice. This
    // avoids false negatives in culling.
    const float distance_bias = 0.0;

    // Find the tiles minimum and maximum distance
    float min_distance = get_distance_from_slice(cell_slice) - distance_bias;
    float max_distance = get_distance_from_slice(cell_slice + 1) + distance_bias;

    // Get the offset in the per-cell light list
    int storage_offs = (LC_MAX_LIGHTS_PER_CELL + 1) * idx;
    int num_rendered_lights = 0;

    // Compute sample directions
    vec3 local_ray_dirs[num_raydirs] = get_raydirs(cell_x, cell_y, precompute_size);

    // Get amount of visible lights in frustum
    int max_frustum_lights = texelFetch(FrustumLights, 0).x;

    // Cull all lights
    for (int i = 0; i < max_frustum_lights && num_rendered_lights < LC_MAX_LIGHTS_PER_CELL; i++) {
        int light_index = texelFetch(FrustumLights, i + 1).x;

        // Fetch data of current light
        LightData light_data = read_light_data(AllLightsData, light_index);

        // Get Light position and project it to view space
        vec3 light_pos = get_light_position(light_data);
        vec4 light_pos_view = MainSceneData.view_mat_z_up * vec4(light_pos, 1);

        bool visible = false;

        // Get a sphere encapsulating the light and cull against that
        Sphere sphere = get_representative_sphere(light_data);
        for (int k = 0; k < num_raydirs; ++k) {
            visible = visible || viewspace_ray_sphere_distance_intersection(
                sphere, local_ray_dirs[k], min_distance, max_distance);
        }

        // Uncomment this to see if the culling produces any issues
        // visible = true;

        // Write the light to the light buffer
        if (visible) {
            // Add one since the first element is the counter storing the total count
            imageStore(PerCellLightsBuffer, storage_offs + 1 + num_rendered_lights, ivec4(light_index));
            ++num_rendered_lights;
        }
    }

    // Write the total light count
    imageStore(PerCellLightsBuffer, storage_offs, ivec4(num_rendered_lights));
}
