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

uniform sampler2D SourceTex;
uniform int sourceMip;
uniform writeonly image2D RESTRICT DestTex;

const int num_steps = 2;
CONST_ARRAY float blur_weights[num_steps] = float[num_steps](
  0.916459570256, 0.0835404297438
);

CONST_ARRAY float blur_offsets[num_steps] = float[num_steps](
  0.377540668798, 2.07585818002
);

void main() {
  vec2 texsize = textureSize(SourceTex, sourceMip).xy;
  vec2 texcoord = vec2(ivec2(gl_FragCoord.xy) * 2 + 1.0) / texsize;

  // TODO: Split into vertical and horizontal pass .. this is quite slow
  // TODO: Normalize gaussian weights

  float total_weight = 0.0;
  vec4 accum = vec4(0);
  const int kernel_steps = num_steps - 1;

  for (int px = 0; px <= 1; ++px) {
    for (int i = 0; i <= kernel_steps; ++i) {
      for (int py = 0; py <= 1; ++py) {
        for (int j = 0; j <= kernel_steps; ++j) {
          float weight = blur_weights[i] * blur_weights[j];
          vec2 offs = vec2(blur_offsets[i], blur_offsets[j]) / texsize;
          offs *= vec2(px, py) * 2 - 1;
          accum += textureLod(SourceTex, texcoord + offs, sourceMip) * weight;
          total_weight += weight;
        }
      }
    }
  }

  accum /= total_weight;
  imageStore(DestTex, ivec2(gl_FragCoord.xy), accum);
}
