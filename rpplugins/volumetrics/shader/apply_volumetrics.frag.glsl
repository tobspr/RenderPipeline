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

const float fog_start = 0.0;
const float fog_end = TimeOfDay.volumetrics.height_fog_scale;

bool is_in_fog(vec3 pos) {
  const float hfog_lower_bounds = fog_start;
  const float hfog_upper_bounds = fog_end;
  return pos.z >= hfog_lower_bounds && pos.z <= hfog_upper_bounds;
}

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

  // if (is_skybox(surface_pos)) {
  //   result = scene_color;
  //   return;
  // }

  vec3 fog_color = TimeOfDay.volumetrics.fog_color / 255.0 * 5.0 * TimeOfDay.volumetrics.fog_brightness;
  
  float fog_weight = 0.0;
  float fog_ramp = TimeOfDay.volumetrics.fog_ramp_size;
  float ground_fog_factor = TimeOfDay.volumetrics.height_fog_scale;

  const float hfog_lower_bounds = fog_start;
  const float hfog_upper_bounds = fog_end;

  vec3 start_pos, end_pos;
  vec3 ray_dir = normalize(MainSceneData.camera_pos - surface_pos);

  if (surface_pos.z > MainSceneData.camera_pos.z) {
    // Flip start and end pos if surface above camera
    start_pos = surface_pos;
    end_pos = MainSceneData.camera_pos;
    ray_dir = -ray_dir;
  } else {
    start_pos = MainSceneData.camera_pos;    
    end_pos = surface_pos;
  }

  float dist_to_surface = distance(MainSceneData.camera_pos, surface_pos);


  // Prevent NaN's
  if ( abs(ray_dir.z) < 1e-3) ray_dir.z = 1e-3;

  // float advance_end = (end_pos.z - hfog_lower_bounds) / ray_dir.z;

  // if (advance_start < 0.0) {
  //   result = vec3(1, 0, 0);
  //   return;
  // }

  // advance_end = clamp(advance_end, 0.0, dist_to_surface);

  // if (advance_start < 0.0) advance_start = 0.0;
  // if (advance_end < 0.0) {
  //   fog_weight = 0.0;
  // } else {

  // vec3 start_clip = start_pos + advance_start * ray_dir;
  // vec3 end_clip = end_pos + advance_end * ray_dir;



  // Clamp to bounds
  if (!is_in_fog(start_pos)) {
    float advance_start = (start_pos.z - hfog_upper_bounds) / ray_dir.z;
    advance_start = min(advance_start, dist_to_surface);
    start_pos = start_pos - advance_start * ray_dir;
  }

  // Clamp to bounds
  if (!is_in_fog(end_pos)) {
    float advance_end = (end_pos.z - hfog_lower_bounds) / ray_dir.z;
    advance_end = min(advance_end, dist_to_surface);
    // end_pos = end_pos + advance_end * ray_dir;

  }

  // fog_weight = saturate( distance(start_pos, end_pos) / fog_ramp );

  // }
  fog_weight = saturate(1.0 - exp(-distance(start_pos, end_pos) / fog_ramp));

  // const float b = 1.0 / 1500.0;
  // start_pos = MasinSceneData.camera_pos;
  // end_pos = surface_pos;
  // float exp_height_fog = exp(-start_pos.z * b) * (1.0 - exp(-distance(start_pos, end_pos) * ray_dir.z * b )) / ray_dir.z;

  // fog_weight = exp_height_fog;

  // result = vec3(fog_weight);
  // return;

  // float hfog_start = min(MainSceneData.camera_pos.z, surface_pos.z);
  // float hfog_end = max(MainSceneData.camera_pos.z, surface_pos.z);

  // hfog_start = clamp(hfog_start, hfog_lower_bounds, hfog_upper_bounds);
  // hfog_end = clamp(hfog_end, hfog_lower_bounds, hfog_upper_bounds);

  // float fog_lower = 1.0 - saturate(hfog_start / ground_fog_factor);
  // float fog_upper = 1.0 - saturate(hfog_end / ground_fog_factor);
  // float fog_travel_vertical = fog_lower - fog_upper;

  // float fog_travel_horizontal = saturate(distance(MainSceneData.camera_pos.xy, surface_pos.xy) / fog_ramp);
    // float weight = saturate(1.0 - exp(-distance(sample_pos, MainSceneData.camera_pos) / fog_ramp));

  // float fog_travel_total = fog_travel_horizontal;

  // fog_weight = fog_travel_total;
  // float hfog_amount = hfog_start - hof

  // for (int i = 0; i < num_steps; ++i) {

    // vec3 sample_pos = curr_pos + pow(float(i) / (num_steps - 1), 1.5) * step_dir;

    // // Distance fog

    // // Exponential height fog

    // fog_weight += weight;


  // fog_weight /= num_steps;
  // fog_weight = saturate(fog_weight * fog_density);

  #if !DEBUG_MODE
    merged_color = mix(merged_color, fog_color, fog_weight);
  #endif



  result = merged_color;
}
