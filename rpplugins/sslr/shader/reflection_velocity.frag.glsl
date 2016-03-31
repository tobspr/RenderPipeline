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
#pragma include "includes/color_spaces.inc.glsl"
#pragma include "includes/gbuffer.inc.glsl"
#pragma include "includes/transforms.inc.glsl"

uniform sampler2D CombinedVelocity;
uniform sampler2D TraceResult;
uniform sampler2D Previous_SceneDepth;

// Copies the reflection velocity vector

out vec4 result;

void main() {
  vec2 texcoord = get_texcoord();
  // vec2 velocity = texture(CombinedVelocity, texcoord).xy;
  // vec2 last_coord = texcoord + velocity;

  vec3 best_result = vec3(0);

  // Take intersection with most weight
  const int kernel_size = 1;
  for (int i = -kernel_size; i <= kernel_size; ++i) {
    for (int j = -kernel_size; j <= kernel_size; ++j) {
      vec3 trace_result = texture(TraceResult, truncate_coordinate(texcoord + vec2(i, j) * 2.0 / SCREEN_SIZE)).xyz;
      if (trace_result.z > best_result.z) {
        best_result = trace_result;
      }
    }
  }
  
  if (length_squared(best_result.xy) < 1e-4) {
    best_result.xy = texcoord;
  }

  vec2 velocity = texture(CombinedVelocity, best_result.xy).xy;
  result = vec4(velocity, 0, 1);
}
