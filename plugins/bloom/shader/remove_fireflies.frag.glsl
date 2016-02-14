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
#pragma include "render_pipeline_base.inc.glsl"
#pragma include "includes/gaussian_weights.inc.glsl"
#pragma include "includes/color_spaces.inc.glsl"

uniform sampler2D SourceTex;
out vec3 result;

// Karis average
float get_weight(vec3 color, float weight) {
    return weight / (1.0 + get_luminance(color));
}

uniform ivec2 direction;

void main() {

    vec2 texcoord = get_texcoord();

    #if GET_SETTING(bloom, remove_fireflies)
        float weights = 0.0;
        vec3 accum = vec3(0);
        const int filter_size = 5;

        vec2 texel_offs = direction / SCREEN_SIZE;

        // Find all surrounding pixels and weight them
        for (int i = -filter_size; i <= filter_size; ++i) {
            vec3 color_sample = textureLod(SourceTex, texcoord + i * texel_offs, 0).xyz;
            float weight = get_weight(color_sample, gaussian_weights_6[abs(i)]);
            accum += color_sample * weight;
            weights += weight;
        }

        accum /= max(0.01, weights);
        result = accum;
    #else
        result = textureLod(SourceTex, texcoord, 0).xyz;
    #endif
}
