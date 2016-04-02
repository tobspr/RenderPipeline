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

uniform sampler2D SourceTex;

// Filters the SSR result and removes single pixels

out vec4 result;

void main() {
  vec2 texcoord = get_half_texcoord();
  vec2 pixsize = 2.0 / SCREEN_SIZE;

  vec4 mid_data = texture(SourceTex, texcoord);

  // result = mid_data;
  // return;

  // Skip lost pixels
  if (mid_data.w < 1e-3) {
    result = vec4(0);
    return;
  }

  const int kernel_size = 1;

  int num_adjacent_pixels = 0;
  for (int x = -kernel_size; x <= kernel_size; ++x) {
    for (int y = -kernel_size; y <= kernel_size; ++y) {
      if (x == 0 && y == 0) continue;
      if (distance(texture(SourceTex, texcoord + vec2(x, y) * pixsize).xyz, mid_data.xyz) < 0.05) {
        num_adjacent_pixels ++;
      }
    }
  }

  if (num_adjacent_pixels < 2) {
    mid_data *= 0;
  }
  result = mid_data;
}
