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
#pragma include "includes/brdf.inc.glsl"
#pragma include "includes/transforms.inc.glsl"
#pragma include "includes/importance_sampling.inc.glsl"

uniform sampler2D DownscaledDepth;

out vec3 result;

#define USE_LINEAR_DEPTH 0
#define NUM_RAYDIR_RETRIES 3

const int num_steps = 64;
const float hit_tolerance_ws = 0.0;
const float hit_tolerance_backface = 0.0003;

bool point_between_planes(float z, float z_a, float z_b, out bool hit_factor) {

    // This traces correct, but looks weird because gaps are not filled
    // return z + hit_tolerance_ws >= min(z_a, z_b) - 0.00015 && z - hit_tolerance_ws <= max(z_a, z_b);

    hit_factor = false;

    // This traces "incorrect", but looks better because gaps are getting filled then
    if (z - hit_tolerance_ws <= max(z_a, z_b)) {
        hit_factor = z + hit_tolerance_ws >= min(z_a, z_b) - hit_tolerance_backface;
        hit_factor = true;
        return true;
    }

    return false;
}


void main()
{
    ivec2 coord = ivec2(gl_FragCoord.xy);
    vec2 texcoord = get_half_texcoord();

    // TODO: Using the real normal provides *way* worse coherency
    vec3 normal_vs = get_view_normal(texcoord);
    Material m = unpack_material(GBuffer, texcoord);
    normal_vs = world_normal_to_view(m.normal);

    vec3 ray_start_vs = get_view_pos_at(texcoord);
    float pixeldist = distance(m.position, MainSceneData.camera_pos);

    // Skip skybox
    if (pixeldist > 3000) {
        result = vec3(0);
        return;
    }

    // Get ray start
    vec3 view_dir = normalize(ray_start_vs);
    vec3 ray_dir = normalize(reflect(view_dir, normal_vs));

    // Get tangent and binormal
    vec3 tangent, binormal;
    find_arbitrary_tangent(ray_dir, tangent, binormal);


    float pdf = 0.0;
    vec3 importance_ray_dir = vec3(0);

    float roughness = get_effective_roughness(m);

    // Generate ray directions until we find a value which is valid
    for (int i = 0; i < NUM_RAYDIR_RETRIES; ++i) {

        vec2 seed = texcoord + 0.3123 * i + 0.633 * (MainSceneData.frame_index % 8);

        // Get random sequence, should probably use halton or so
        vec2 xi = clamp(abs(rand_rgb(seed).xz), vec2(0.01), vec2(0.99));

        // Clamp brdf tail, see frostbite slides for details
        const float brdf_bias = 0.7;
        xi.y = mix(xi.y, 0.0, brdf_bias);

        // Get importance sampled directory
        vec4 rho = importance_sample_ggx(xi, clamp(roughness, 0.0001, 1.0));

        importance_ray_dir = normalize(
            1e-5 + rho.x * tangent + rho.y * binormal + rho.z * ray_dir);
        pdf = rho.w;

        // If the ray dir is fine, abort, otherwise continue
        if (dot(ray_dir, normal_vs) > 0.01 && pdf > 0.001) {
            break;
        }
    }

    ray_dir = importance_ray_dir;

    if (dot(ray_dir, normal_vs) <= 0.0 && pdf >= 0.0001) {
        // Failed to find valid sample - thats bad!
        result = vec3(0);
        return;
    }

    // Ray not in view
    if (dot(ray_dir, view_dir) < 1e-5) {
        result = vec3(0,0,0);
        return;
    }

    float RxV = dot(ray_dir, view_dir);
    float max_ray_len = 10.0 * pixeldist;

    // Clip ray to near plane
    float ray_len = ((ray_start_vs.z + ray_dir.z * max_ray_len) > CAMERA_NEAR) ?
                        (CAMERA_NEAR - ray_start_vs.z) / ray_dir.z :
                        max_ray_len;
    // ray_len = max_ray_len;


    // Convert start and end pos from view to screen space
    vec3 ray_start_screen = view_to_screen(ray_start_vs);
    vec3 ray_end_screen = view_to_screen(ray_start_vs + ray_len * ray_dir);

    vec3 ray_pos = ray_start_screen;
    vec3 ray_dir_screen = ray_end_screen - ray_start_screen;


    // Make sure the ray does not leave the screen
    float scale_max_x = min(1, 0.99 * (1.0 - ray_start_screen.x) / max(1e-5, ray_dir_screen.x));
    float scale_max_y = min(1, 0.99 * (1.0 - ray_start_screen.y) / max(1e-5, ray_dir_screen.y));
    float scale_min_x = min(1, 0.99 * ray_start_screen.x / max(1e-5, -ray_dir_screen.x));
    float scale_min_y = min(1, 0.99 * ray_start_screen.y / max(1e-5, -ray_dir_screen.y));
    ray_dir_screen *= min(scale_max_x, scale_max_y);
    ray_dir_screen *= min(scale_min_x, scale_min_y);


    // Linearize depth so we can interpolate it
    #if USE_LINEAR_DEPTH
        ray_start_screen.z = get_linear_z_from_z(ray_start_screen.z);
        ray_end_screen.z = get_linear_z_from_z(ray_end_screen.z);
    #endif

    vec3 ray_step = (ray_end_screen - ray_start_screen) / num_steps;
    ray_pos += 0.2 * ray_step * float(num_steps) / 512.0 / saturate(dot(normal_vs, -view_dir));

    vec2 intersection = vec2(-1);

    // float jitter = rand(texcoord + MainSceneData.temporal_index);
    float jitter = abs(rand(ivec2(gl_FragCoord.xy) + (MainSceneData.frame_index % 8) * 0.1));
    // jitter *= 0.0;
    jitter *= 2.0;
    ray_pos += jitter * ray_step;

    int i;
    float intersection_weight = 0.0;
    bool hit_factor = false;
    for (i = 1; i < num_steps; ++i) {
        ray_pos += ray_step;

        // Current coordinate is in the mid of two samples, not at the end, so
        // substract half of a step
        vec2 curr_coord = ray_pos.xy - 0.5 * ray_step.xy;

        // Check for intersection
        #if USE_LINEAR_DEPTH
            float depth_sample = textureLod(DownscaledDepth, curr_coord, 0).x;
        #else
            float depth_sample = textureLod(GBuffer.Depth, curr_coord, 0).x;
        #endif

        if (point_between_planes(depth_sample, ray_pos.z, ray_pos.z - ray_step.z, hit_factor)) {
            intersection = curr_coord;
            break;
        }
    }

    intersection = truncate_coordinate(intersection);

    // Check if we hit something
    if (min(intersection.x, intersection.y) <= 0.0) {
        // result = vec3(0.2, 0, 0, 0);
        result = vec3(0);
        return;
    }

    // Out of screen, can early out
    if (out_of_screen(intersection)) {
        // result = vec3(0, 1, 0, 0);
        result = vec3(0);
        return;
    }

    float fade = saturate(5.0 * RxV);
    // float fade = pow(1 - (i / float(num_steps - 1)), 1);
    if (fade < 1e-3) {
        result = vec3(0);
        return;
    }

    // XXX
    if (!hit_factor) {
        result = vec3(0);
        return;
    }

    // float depth_at_intersection = textureLod(GBuffer.Depth, intersection.xy, 0).x;
    // if (get_linear_z_from_z(depth_at_intersection) > 3000.0) {
    //     result = vec3(0);
    //     return;
    // }

    fade = 1.0;
    pdf = 1.0;

    result = vec3(intersection, 1.0 / max(1e-5, pdf) * fade);
}

