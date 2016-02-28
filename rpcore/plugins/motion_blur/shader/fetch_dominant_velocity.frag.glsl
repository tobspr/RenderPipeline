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

#define USE_MAIN_SCENE_DATA
#define USE_GBUFFER_EXTENSIONS
#pragma include "render_pipeline_base.inc.glsl"
#pragma include "includes/gbuffer.inc.glsl"

out vec2 result;

void main() {

  const int tile_size = GET_SETTING(motion_blur, tile_size);
  const float blur_factor = GET_SETTING(motion_blur, blur_factor);
  const float maxlen = GET_SETTING(motion_blur, max_blur_radius) * tile_size / WINDOW_WIDTH;


  ivec2 coord = ivec2(gl_FragCoord.xy);
  ivec2 screen_coord = coord * tile_size;

  vec2 max_velocity = vec2(0);
  float max_velocity_len_sq = 0.0;

  // TODO: Seperate this pass in x- and y- directions

  // Find the longest vector in the tile
  for (int x = 0; x < tile_size; x += 4) {
    for (int y = 0; y < tile_size; y += 4) {
      ivec2 coord = clamp(screen_coord + ivec2(x, y), ivec2(0), SCREEN_SIZE_INT - 1);
      vec2 velocity = get_gbuffer_velocity(GBuffer, coord);
      float len_sq = dot(velocity, velocity);

      // Check if the vector is longer than the current longest vector
      if (len_sq > max_velocity_len_sq) {
        max_velocity_len_sq = len_sq;
        max_velocity = velocity;
      }
    }
  }

  max_velocity *= blur_factor;

  // Make sure the velocity does not exceed the maximum length
  float vel_len = length(max_velocity);
  if (vel_len > maxlen) {
    max_velocity *= maxlen / vel_len;
  }

  result = max_velocity;
}
