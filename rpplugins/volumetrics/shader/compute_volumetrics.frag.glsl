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
#define USE_TIME_OF_DAY
#define USE_GBUFFER_EXTENSIONS
#pragma include "render_pipeline_base.inc.glsl"
#pragma include "includes/gbuffer.inc.glsl"
#pragma include "includes/shadows.inc.glsl"
#pragma include "includes/noise.inc.glsl"

#pragma optionNV (unroll all)

uniform sampler2D ShadedScene;

#if HAVE_PLUGIN(pssm)
uniform mat4 PSSMSceneSunShadowMVP;
uniform sampler2DShadow PSSMSceneSunShadowMapPCF;
#endif

out vec4 result;

void main() {

  #if DEBUG_MODE
    result = vec4(0);
    return;
  #endif

  vec2 texcoord = get_half_texcoord();

  vec3 start_pos = MainSceneData.camera_pos;
  vec3 end_pos = get_gbuffer_position(GBuffer, texcoord);

  float max_distance = 50.0;

  vec3 step_vector = (end_pos - start_pos);
  if (length(step_vector) > max_distance) {
    step_vector = normalize(step_vector) * max_distance;
  }

  end_pos = start_pos + step_vector;

  float jitter = rand(ivec2(gl_FragCoord.xy) % 2);

  const int num_steps = 32;
  vec3 step_offs = step_vector / num_steps;

  vec4 volumetrics = vec4(0);
  float volume_density = 0.00015;
  // float volume_density = 0.0003;

  vec3 sun_color = get_sun_color();
  vec3 sun_vector = get_sun_vector();

  const float slope_bias =  0.0 * 0.02;
  const float normal_bias = 0.0;
  const float fixed_bias =  0.01 * 0.001;

  for (int i = 0; i < num_steps; ++i) {
    vec3 pos = start_pos + (i + jitter) * step_offs;
    pos = get_biased_position(pos, slope_bias, normal_bias, vec3(0), sun_vector);

    vec3 projected = project(PSSMSceneSunShadowMVP, pos);
    projected.z -= fixed_bias;

    float shadow_term = texture(PSSMSceneSunShadowMapPCF, projected).x;
    if (out_of_unit_box(projected)) {
      // break;
      shadow_term = 1;
    }

    vec4 color = vec4(sun_color, 1) * volume_density * shadow_term;
    volumetrics += color * (1 - volumetrics.w);
  }

  // volumetrics.xyz = pow(volumetrics.xyz * 2.0, vec3(2.0));
  volumetrics.w *= 100.0;

  vec3 scene_color = texture(ShadedScene, texcoord).xyz;
  result = volumetrics;
}
