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


#pragma include "render_pipeline_base.inc.glsl"

in vec4 p3d_Vertex;

flat out vec2 sun_pos_tc;
flat out float godray_factor;

void main() {

    // Compute texture coordinates of the sun-disk
    vec3 sun_vector = get_sun_vector();
    vec3 sun_pos = sun_vector * 1e20;
    vec4 sun_proj = MainSceneData.view_proj_mat_no_jitter * vec4(sun_pos, 1);
    sun_proj.xyz /= sun_proj.w;
    if (sun_proj.w < 0.0) {
        // Discard vertex when sun not on screen
        return;
    }
    sun_pos_tc = sun_proj.xy * 0.5 + 0.5;
    godray_factor = compute_screen_fade_factor(sun_pos_tc, 0.02);


    gl_Position = vec4(p3d_Vertex.xz, 0, 1);
}
