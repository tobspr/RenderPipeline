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
#pragma include "includes/noise.inc.glsl"

#pragma optionNV (unroll all)

uniform sampler2D SourceTex;
out vec3 result;

const int num_samples = GET_SETTING(motion_blur, num_camera_samples);

void main() {

  vec2 texcoord = get_texcoord();
  ivec2 coord = ivec2(gl_FragCoord.xy);

  // Reconstruct last frame texcoord
  vec2 film_offset_bias = MainSceneData.current_film_offset * vec2(1.0,1.0 / ASPECT_RATIO);
  vec3 pos = get_world_pos_at(texcoord + film_offset_bias);
  vec4 last_proj = MainSceneData.last_view_proj_mat_no_jitter * vec4(pos, 1);
  vec2 last_coord = fma(last_proj.xy / last_proj.w, vec2(0.5), vec2(0.5));

  // Compute velocity in screen space
  vec2 velocity = last_coord - texcoord;
  float velocity_len = length(velocity);

  // Make sure that when we have low-fps, we reduce motion blur, and when we
  // have higher fps, we increase it - this way it perceptually always stays
  // the same (otherwise it feels really laggy at low FPS)
  float target_fps = 60.0;
  velocity *= (1.0 / target_fps) / MainSceneData.smooth_frame_delta;
  velocity *= GET_SETTING(motion_blur, camera_blur_factor);

  // We can abort early when no velocity is present
  if (velocity_len < 0.505 / WINDOW_WIDTH) {
    result = texture(SourceTex, texcoord, 0).xyz;
    return;
  }

  vec3 accum = vec3(0);
  float jitter = rand(texcoord) * 2.0 - 1.0;

  // Take two samples at a time
  for (int i = -num_samples + 1; i < num_samples; ++i) {
    vec2 offs = (i + 0.5 * jitter) / float(num_samples) * velocity;
    accum += texture(SourceTex, texcoord + offs).xyz;
  }

  accum /= float(2 * (num_samples - 1) + 1);
  result = saturate(accum);
}
