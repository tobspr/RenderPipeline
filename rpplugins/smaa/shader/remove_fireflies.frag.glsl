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
#pragma optionNV (unroll all)

#define USE_MAIN_SCENE_DATA
#define USE_GBUFFER_EXTENSIONS
#pragma include "render_pipeline_base.inc.glsl"
#pragma include "includes/gaussian_weights.inc.glsl"
#pragma include "includes/gbuffer.inc.glsl"
#pragma include "includes/color_spaces.inc.glsl"

uniform sampler2D ShadedScene;
out vec3 result;

// Removes single bright pixels to improve antialiasing

void main() {
    vec2 texcoord = get_texcoord();
    vec3 accum = vec3(0);
    const int filter_size = 1;

    vec2 texel_offs = 1.0 / SCREEN_SIZE;
    vec3 center_pixel = textureLod(ShadedScene, texcoord, 0).xyz;
    float center_luminance = get_luminance(center_pixel);
    float center_depth = get_depth_at(texcoord);
    vec3 avg_color = vec3(0);
    float weights = 0.0;

    const float max_depth_diff = 0.0002;

    // Find all surrounding pixels and weight them
    for (int i = -filter_size; i <= filter_size; ++i) {
        for (int j = -filter_size; j <= filter_size; ++j) {
            // if (abs(i) + abs(j) > 1) continue;
            vec2 offcoord = texcoord + vec2(i, j) * texel_offs;
            vec3 color_sample = textureLod(ShadedScene, offcoord, 0).xyz;
            float depth_sample = get_depth_at(offcoord);
            float weight = 1.0 - saturate(abs(depth_sample - center_depth) / max_depth_diff);

            // Weight the center sample multiple times
            if (i == 0 && j == 0) {
                weight = 3;
            }

            avg_color += color_sample * weight;
            weights += weight;
        }
    }

    avg_color /= max(1e-5, weights);
    result = avg_color;
}
