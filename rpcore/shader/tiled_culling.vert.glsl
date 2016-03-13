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

#version 400

#define USE_MAIN_SCENE_DATA
#pragma include "render_pipeline_base.inc.glsl"
#pragma include "includes/transforms.inc.glsl"

in vec4 p3d_Vertex;
uniform isamplerBuffer CellListBuffer;

// Order: BL BR TL TR
flat out mat4 frustumCorners;

void main() {

    // Find the amount of cells to shade
    int num_total_cells = texelFetch(CellListBuffer, 0).x;

    // Compute the amount of pixel lines required to shade all cells
    int num_used_slices = int(ceil(float(num_total_cells) / LC_CULLING_SLICE_WIDTH));

    // Compute the percentage factor of the used slices
    float percentage_height = num_used_slices / float(LC_SHADE_SLICES);

    // Store the vertex position.
    gl_Position = vec4(p3d_Vertex.x, fma(fma(p3d_Vertex.z, 0.5, 0.5) * percentage_height, 2.0, -1.0) , 0, 1);

    // Pass frustum corners to the culling shader
    frustumCorners = mat4(
      vec4(calculate_view_pos(1, vec2(0, 0)), 1), // bl
      vec4(calculate_view_pos(1, vec2(1, 0)), 1), // br
      vec4(calculate_view_pos(1, vec2(0, 1)), 1), // tl
      vec4(calculate_view_pos(1, vec2(1, 1)), 1)  // tr
    );

}
