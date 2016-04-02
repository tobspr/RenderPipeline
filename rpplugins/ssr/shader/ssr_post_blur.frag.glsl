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

#define USE_MAIN_SCENE_DATA
#define USE_GBUFFER_EXTENSIONS
#pragma include "render_pipeline_base.inc.glsl"
#pragma include "includes/GBuffer.inc.glsl"

uniform sampler2D CurrentTex;
out vec4 result;

void main() {
    vec2 texcoord = get_texcoord();

    const int filter_size = 1;

    float mid_depth = get_depth_at(texcoord);

    vec4 accum = vec4(0);
    float weights = 0.0;

    const float max_depth_diff = 0.001;

    for (int i = -filter_size; i <= filter_size; ++i) {
      for (int j = -filter_size; j <= filter_size; ++j) {
        vec2 offcoord = texcoord + vec2(i, j) / SCREEN_SIZE;
        vec4 sample_color = texture(CurrentTex, offcoord);
        float sample_depth = get_depth_at(texcoord);
        float weight = 1.0 - saturate(abs(sample_depth - mid_depth) / max_depth_diff);
        accum += sample_color * weight;
        weights += weight;

      }
    }

    accum /= max(1e-5, weights);
    result = accum;
}
