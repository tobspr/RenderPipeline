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
#pragma include "includes/transforms.inc.glsl"
#pragma include "includes/gbuffer.inc.glsl"

uniform sampler2D CurrentTex;
uniform sampler2D VelocityTex;
uniform sampler2D CurrentTrace;
uniform sampler2D CombinedVelocity;
uniform sampler2D Previous_SceneDepth;
uniform sampler2D Previous_SSLRSpecular;
uniform sampler2D Previous_SSLRTraceResult;

#define RS_MAX_CLIP_DIST 3.0
#define RS_DISTANCE_SCALE 0.2
#define RS_KEEP_GOOD_DURATION 10.0
#define RS_KEEP_BAD_DURATION 10.0
#define RS_AABB_SIZE 2.0

#pragma include "includes/temporal_resolve.inc.glsl"

out vec4 result;

void main() {
    vec2 texcoord = get_texcoord();
    // vec2 velocity = texture(CombinedVelocity, texcoord).xy;
    vec2 velocity = texture(VelocityTex, texcoord).xy;
    vec2 last_coord = texcoord + velocity;

    if (out_of_screen(last_coord)) {
      result = texture(CurrentTex, texcoord);
      return;
    }

    result = resolve_temporal(CurrentTex, Previous_SSLRSpecular, texcoord, last_coord);
    return;


    // This following is a data driven resolve approach.
    // It resolves the exact color, however leads to *tons* of noise, due to
    // missing samples. It seems that using a pure-color based approach works
    // much better.

    /*


    // Get material data
    Material m = unpack_material(GBuffer, texcoord);
    vec3 view_vector = normalize(MainSceneData.camera_pos - m.position);
    vec3 reflected_dir = get_reflection_vector(m, -view_vector);
    float roughness = get_effective_roughness(m);

    vec4 curr_color = texture(CurrentTex, texcoord);
    vec4 last_color = texture(Previous_SSLRSpecular, last_coord);

    float weight = 1.0 / 8.0;

    vec3 prev_intersect = texture(Previous_SSLRTraceResult, last_coord).xyz;

    float prev_intersect_depth = texture(Previous_SceneDepth, prev_intersect.xy).x;
    vec3 prev_intersect_pos = calculate_surface_pos(prev_intersect_depth, prev_intersect.xy, MainSceneData.last_inv_view_proj_mat_no_jitter);

    vec3 current_intersection = texture(CurrentTrace, texcoord).xyz;
    float current_intersection_depth = get_depth_at(current_intersection.xy);
    vec3 current_intersection_pos = calculate_surface_pos(current_intersection_depth, current_intersection.xy);
    vec4 accum = vec4(0);

    float current_refl_length = distance(current_intersection_pos, m.position);
    float last_refl_length = distance(prev_intersect_pos, m.position);

    const float max_refl_dist = 0.4;

    {
      vec3 prev_reflection = normalize(prev_intersect_pos - m.position);
      vec3 h = normalize(view_vector + prev_reflection);
      float NxH = clamp(dot(m.normal, h), 1e-4, 1.0);
      float brdf_weight = clamp(brdf_distribution_ggx(NxH, roughness), 0.0, 1.0);
      // float brdf_weight = clamp(brdf_distribution_ggx(NxH, 0.02), 0.0, 1.0);
      // accum += brdf_weight * last_color * prev_intersect.z * 8.0;
      brdf_weight = 1;

      // xxx
      // brdf_weight *= 1.0 - saturate(abs(current_refl_length - last_refl_length) / max_refl_dist );
      brdf_weight *= step(abs(current_refl_length - last_refl_length), max_refl_dist);

      // accum += brdf_weight * last_color * prev_intersect.z * 9.0;
      accum += brdf_weight * last_color * 9.0;
    }

    accum += curr_color * 1.0;

    // accum /= max(1.0, accum.w);
    // accum /= 10.0;

    // result = vec4(accum);

    result = mix(last_color, curr_color, weight);
    */
}
