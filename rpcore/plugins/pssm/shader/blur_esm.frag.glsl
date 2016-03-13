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

// Blurs the ESM

#pragma include "render_pipeline_base.inc.glsl"
#pragma include "includes/gaussian_weights.inc.glsl"

uniform sampler2D SourceTex;
uniform ivec2 direction;

out float result;

void main() {
  vec2 texsize = textureSize(SourceTex, 0).xy;
  vec2 texcoord = gl_FragCoord.xy / texsize;

  float accum = 0;
  const int num_steps = 4;
  for (int i = -num_steps; i <= num_steps; ++i) {
      vec2 offs = vec2(i * direction) / texsize;
      accum += textureLod(SourceTex, texcoord + offs, 0).x * gaussian_weights_5[abs(i)];
  }

  result = accum;
}
