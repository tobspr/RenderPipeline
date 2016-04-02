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

// Filters the SSR result and fills in holes

out vec4 result;

bool can_merge_data(vec4 point_a, vec4 point_b) {
  if (point_a.w > 1e-3 && point_b.w > 1e-3) {
    return distance(point_a.xyz, point_b.xyz) < 0.01;
  }
  return false;
}

void main() {
  vec2 texcoord = get_half_texcoord();
  vec2 pixsize = 2.0 / SCREEN_SIZE;

  vec4 mid_data = texture(SourceTex, texcoord);
  float mid_weight = mid_data.x > 1e-5 ? 1 : 0;

  // result = mid_data;
  // return;

  if (mid_data.w >= 1e-3) {
    result = mid_data;
    return;
  }

  // Try to take a sample from the top and bottom
  vec4 sample_top = texture(SourceTex, texcoord + vec2(0, 1) * pixsize);
  vec4 sample_bottom = texture(SourceTex, texcoord + vec2(0, -1) * pixsize);

  if (can_merge_data(sample_top, sample_bottom)) {
    result = (sample_top + sample_bottom) * 0.5;
    return;
  }

  // If that fails, take a sample from the left and right
  vec4 sample_right = texture(SourceTex, texcoord + vec2(1, 0) * pixsize);
  vec4 sample_left = texture(SourceTex, texcoord + vec2(-1, 0) * pixsize);

  if (can_merge_data(sample_right, sample_left)) {
    result = (sample_right + sample_left) * 0.5;
    return;
  }

  // Seems we have no neighbours, check if we can find something diagonally
  vec4 sample_tl = texture(SourceTex, texcoord + vec2(-1, 1) * pixsize);
  vec4 sample_br = texture(SourceTex, texcoord + vec2(1, -1) * pixsize);

  if (can_merge_data(sample_tl, sample_br)) {
    result = (sample_tl + sample_br) * 0.5;
    return;
  }

  // Check the other diagonal
  vec4 sample_tr = texture(SourceTex, texcoord + vec2(1, 1) * pixsize);
  vec4 sample_bl = texture(SourceTex, texcoord + vec2(-1,-1) * pixsize);

  if (can_merge_data(sample_tr, sample_bl)) {
    result = (sample_tl + sample_br) * 0.5;
    return;
  }

  // If we arrived here, the pixel cannot get recovered in any way
  result = vec4(0);
}
