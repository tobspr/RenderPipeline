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
#pragma include "includes/gaussian_weights.inc.glsl"

uniform sampler2D ShadedScene;
uniform ivec2 direction;

out vec3 result;

void main() {
    ivec2 coord = ivec2(gl_FragCoord.xy);
    vec2 texcoord = get_texcoord();

    vec2 pixel_offset = 1.0 / SCREEN_SIZE;

    vec3 accum = vec3(0);

    const int num_samples = 20;
    for (int i = 0; i < num_samples; ++i) {
        float weight = opt_gaussian_weights_20[i];
        float offset = opt_gaussian_offsets_20[i];
        vec2 offcoord = texcoord + offset * direction * pixel_offset;
        accum += textureLod(ShadedScene, offcoord, 0).xyz * weight;
    }
    result = accum;
}
