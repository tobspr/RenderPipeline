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

#version 420

#pragma optionNV (unroll all)

#define USE_MAIN_SCENE_DATA
#pragma include "Includes/Configuration.inc.glsl"
#pragma include "Includes/GBuffer.inc.glsl"

out vec4 result;

uniform sampler2D SourceTex;
uniform GBufferData GBuffer;

void main() {

    // Get sample coordinates
    ivec2 coord = ivec2(gl_FragCoord.xy);

    ivec2 bil_start_coord = get_bilateral_coord(coord);

    vec2 bilateral_coord = vec2(bil_start_coord + 0.5) / ivec2(SCREEN_SIZE / 2);
    vec2 main_texcoord = vec2(bil_start_coord * 2 + 0.5) / vec2(SCREEN_SIZE);

    vec2 pixel_size_bil = vec2(1.0) / ivec2(SCREEN_SIZE / 2);
    vec2 pixel_size = 1.0 / SCREEN_SIZE;

    // Get current pixel data
    vec2 texcoord = get_texcoord();
    float mid_depth = get_gbuffer_depth(GBuffer, texcoord);
    vec3 mid_nrm = get_gbuffer_normal(GBuffer, texcoord);

    const float max_depth_diff = 0.00001;
    const float max_nrm_diff = 0.001;

    float weights = 0.0;
    vec4 accum = vec4(0);

    // Accumulate all samples
    for (int x = 0; x < 2; ++x) {
        for (int y = 0; y < 2; ++y) {

            vec2 source_coord = bilateral_coord + vec2(x, y) * 1.0 * pixel_size_bil;
            vec2 screen_coord = main_texcoord + vec2(x, y) * 2.0 * pixel_size;
            vec4 source_sample = textureLod(SourceTex, source_coord, 0);

            // Check how much information those pixels share, and if it is
            // enough, use that sample
            float sample_depth = get_gbuffer_depth(GBuffer, screen_coord);
            vec3 sample_nrm = get_gbuffer_normal(GBuffer, screen_coord);
            float depth_diff = abs(sample_depth - mid_depth) / max_depth_diff;
            float nrm_diff = max(0, dot(sample_nrm, mid_nrm));
            float weight = 1.0 - saturate(depth_diff);
            weight *= pow(nrm_diff, 1.0 / max_nrm_diff);

            // Make sure we don't have a null-weight, but instead only a very
            // small weight, so that in case no pixel matches, we still have
            // data to work with.
            weight = max(0.01, weight);

            accum += source_sample * weight;
            weights += weight;
        }
    }

    accum /= max(0.001, weights);
    result = vec4(accum);
}
