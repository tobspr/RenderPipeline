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

uniform sampler2D SourceTex;
uniform ivec2 direction;
uniform float blurScale;
out vec3 result;

#define BLUR_SEQUENCE opt_gaussian_weights_15

void main() {
    ivec2 coord = ivec2(gl_FragCoord.xy);
    vec2 texcoord = get_texcoord();
    vec2 pixel_offset = blurScale / SCREEN_SIZE;

    vec3 accum = vec3(0);
    for (int i = 0; i < BLUR_SEQUENCE.length(); ++i) {
        vec2 weight_and_offset = BLUR_SEQUENCE [i];
        vec2 offcoord = texcoord + weight_and_offset.y * direction * pixel_offset;
        accum += textureLod(SourceTex, offcoord, 0).xyz * weight_and_offset.x;
    }
    result = accum;
}
