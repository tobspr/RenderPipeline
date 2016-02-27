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


uniform sampler2D ShadedScene;

out vec3 result;

void main() {
  vec2 texcoord = get_texcoord();
  vec2 velocity = get_velocity_at(texcoord);

  const int num_samples = 10;

  float current_fps = 0.5 / MainSceneData.frame_delta;
  const float target_fps = 60.0;

  float sample_size = current_fps / target_fps * 1.0;

  // Blur along both directions
  vec3 accum = vec3(0);
  for(int i = 0; i < num_samples; ++i) {
    float jitter = rand(texcoord);
    vec2 offset = (i + jitter) / float(num_samples) * velocity * sample_size;
    accum += texture(ShadedScene, texcoord + offset, 0).xyz;
    accum += texture(ShadedScene, texcoord - offset, 0).xyz;
  }
  accum /= 2.0 * num_samples;

  result = accum;
}
