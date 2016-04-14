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
#pragma include "render_pipeline_base.inc.glsl"
#pragma include "includes/gbuffer.inc.glsl"
#pragma include "includes/gaussian_weights.inc.glsl"

uniform ivec2 blur_direction;
uniform sampler2D SourceTex;
uniform sampler2D DownscaledDepth;
uniform GBufferData GBuffer;

#define ONLY_RED_COMPONENT 1
#if ONLY_RED_COMPONENT
    #define VALUE_TYPE float
    #define SWIZLLE .x
#else
    #define VALUE_TYPE vec4
    #define SWIZLLE .xyzw
#endif

out VALUE_TYPE result;

const vec2 pixel_size = 2.0 / SCREEN_SIZE;

void do_blur(vec2 coord, uint i, float weight, vec3 pixel_nrm, float pixel_depth, inout VALUE_TYPE accum, inout float accum_w) {
    vec2 offcoord = coord + pixel_size * i * blur_direction;
    VALUE_TYPE sampled = textureLod(SourceTex, offcoord, 0) SWIZLLE ;
    vec3 nrm = get_gbuffer_normal(GBuffer, offcoord);
    float d = texture(DownscaledDepth, offcoord).x;

    weight *= 1.0 - saturate(GET_SETTING(ao, blur_normal_factor) * distance(nrm, pixel_nrm) * 1.0);
    weight *= 1.0 - saturate(GET_SETTING(ao, blur_depth_factor) * abs(d - pixel_depth) * 3);

    accum += sampled * weight;
    accum_w += weight;
}


void main() {
    vec2 texcoord = get_texcoord();

    // Store accumulated color
    VALUE_TYPE accum = VALUE_TYPE(0);
    float accum_w = 0.0;

    // Get the weights array
    const int blur_size = 4;
    CONST_ARRAY float weights[blur_size] = gaussian_weights_4; // <-- this is based on the blur size

    // Get the mid pixel normal and depth
    vec3 pixel_nrm = get_gbuffer_normal(GBuffer, texcoord);
    float pixel_depth = texture(DownscaledDepth, texcoord).x;

    // Blur to the right and left
    for (int i = -blur_size + 1; i < blur_size; ++i) {
        do_blur(texcoord, i, weights[abs(i)], pixel_nrm, pixel_depth, accum, accum_w);
    }

    accum /= max(0.01, accum_w);
    // accum = texelFetch(SourceTex, ivec2(gl_FragCoord.xy), 0);
    result = accum;
}
