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

#define USE_MAIN_SCENE_DATA 1
#define USE_TIME_OF_DAY 1
#define USE_GBUFFER_EXTENSIONS 1
#pragma include "render_pipeline_base.inc.glsl"
#pragma include "includes/gbuffer.inc.glsl"

uniform sampler2D ShadedScene;

#if GET_SETTING(volumetrics, enable_volumetric_shadows)
  uniform sampler2D VolumetricsTex;
#endif

out vec3 result;

void main() {
  vec2 texcoord = get_texcoord();

  float depth = get_depth_at(texcoord);
  vec3 surface_pos = calculate_surface_pos(depth, texcoord);


  #if GET_SETTING(volumetrics, enable_volumetric_shadows)
    vec4 volumetrics = texture(VolumetricsTex, texcoord);
  #else
    vec4 volumetrics = vec4(0);
  #endif

  vec3 scene_color = texture(ShadedScene, texcoord).xyz;

  vec3 merged_color = volumetrics.xyz + scene_color * saturate(1 - volumetrics.w);

  float fog_factor = 1;

  // Distance fog
  float fog_ramp = TimeOfDay.volumetrics.fog_ramp_size;
  fog_factor = saturate(1.0 - exp(-distance(surface_pos, MainSceneData.camera_pos) / fog_ramp));

  // Exponential height fog
  float ground_fog_factor = TimeOfDay.volumetrics.height_fog_scale;
  fog_factor *= 1.0 - saturate( max(0, surface_pos.z) / ground_fog_factor);

  vec3 fog_color = TimeOfDay.volumetrics.fog_color * TimeOfDay.volumetrics.fog_brightness;


  if (is_skybox(surface_pos)) {
    fog_factor = 0;
  }

  merged_color = mix(merged_color, fog_color, fog_factor);

  result = merged_color;
}
