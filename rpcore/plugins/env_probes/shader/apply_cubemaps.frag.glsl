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

#define USE_MAIN_SCENE_DATA
#define USE_GBUFFER_EXTENSIONS
#pragma include "render_pipeline_base.inc.glsl"
#pragma include "includes/gbuffer.inc.glsl"
#pragma include "includes/light_culling.inc.glsl"
#pragma include "includes/envprobes.inc.glsl"


layout(location=0) out vec4 result_spec;
layout(location=1) out vec4 result_diff;


uniform isampler2DArray CellIndices;
uniform isamplerBuffer PerCellProbes;

void main() {
    vec2 texcoord = get_texcoord();
    Material m = unpack_material(GBuffer, texcoord);
    ivec3 tile = get_lc_cell_index(
        ivec2(gl_FragCoord.xy),
        distance(MainSceneData.camera_pos, m.position));

    // Don't shade pixels out of the shading range
    if (tile.z >= LC_TILE_SLICES) {
        result_spec = vec4(0);
        result_diff = vec4(0);
        return;
    }

    int cell_index = texelFetch(CellIndices, tile, 0).x;
    int data_offs = cell_index * MAX_PROBES_PER_CELL;

    vec4 total_diffuse = vec4(0);
    vec4 total_specular = vec4(0);
    float total_weight = 0.0;

    int processed_probes = 0;
    for (int i = 0; i < MAX_PROBES_PER_CELL; ++i) {
        int cubemap_index = texelFetch(PerCellProbes, data_offs + i).x - 1;
        if (cubemap_index < 0) break;
        vec4 diff, spec;
        ++processed_probes;
        total_weight += apply_cubemap(cubemap_index, m, diff, spec);
        total_diffuse += diff;
        total_specular += spec;
    }

    result_spec = total_specular / max(1, total_weight);
    result_diff = total_diffuse / max(1, total_weight);

    // Visualize probe count
    // float probe_factor = processed_probes / MAX_PROBES_PER_CELL;
    // result_spec = vec4(1 - probe_factor, probe_factor, 0, 1);
}
