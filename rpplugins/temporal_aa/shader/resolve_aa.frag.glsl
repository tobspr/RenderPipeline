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

#pragma optionNV (unroll all)

#define RS_MAX_CLIP_DIST 0.4
#define RS_DISTANCE_SCALE 1.5
#define RS_KEEP_GOOD_DURATION float(GET_SETTING(temporal_aa, history_length))
#define RS_KEEP_BAD_DURATION (RS_KEEP_GOOD_DURATION * 1.0)

#pragma include "includes/temporal_resolve.inc.glsl"
#pragma include "includes/color_spaces.inc.glsl"

uniform sampler2D ShadedScene;
uniform sampler2D Previous_TemporalAAPostResolve;
uniform sampler2D CombinedVelocity;

out vec3 result;


vec3 clip_aabb_v3(vec3 aabb_min, vec3 aabb_max, vec3 aabb_center, vec3 q)
{   
    vec3 r = q - aabb_center;
    vec3 rmax = aabb_max - aabb_center.xyz;
    vec3 rmin = aabb_min - aabb_center.xyz;

    const float eps = 1e-8;

    if (r.x > rmax.x + eps)
        r *= (rmax.x / r.x);
    if (r.y > rmax.y + eps)
        r *= (rmax.y / r.y);
    if (r.z > rmax.z + eps)
        r *= (rmax.z / r.z);

    if (r.x < rmin.x - eps)
        r *= (rmin.x / r.x);
    if (r.y < rmin.y - eps)
        r *= (rmin.y / r.y);
    if (r.z < rmin.z - eps)
        r *= (rmin.z / r.z);

    return aabb_center + r;
}

void main() {
    ivec2 coord = ivec2(gl_FragCoord.xy);
    vec2 texcoord = get_texcoord();

    #if DEBUG_MODE
        result = texelFetch(ShadedScene, coord, 0).xyz;
        return;
    #endif

    // Find velocity of closest pixel to get better AA for moving objects
    const int sample_range = 2;

    float depth = get_depth_at(coord);
    ivec2 sample_offset = ivec2(0, 0);
    float closest_depth = depth;

    for (int x = 0; x < 2; ++x) {
        for (int y = 0; y < 2; ++y) {
            ivec2 offs = ivec2(x * 2 - 1, y * 2 - 1) * sample_range;
            float cmp_depth = get_depth_at(coord + offs);
            if (cmp_depth < closest_depth) {
                closest_depth = cmp_depth;
                sample_offset = offs;
            }
        }
    }
    
    // We need to also modify the velocity, if we sample at a different position
    vec2 velocity_offset = sample_offset / SCREEN_SIZE;

    // sample_offset = ivec2(0, 0);

    // Read in velocity
    vec2 velocity = texelFetch(CombinedVelocity, coord + sample_offset, 0).xy;
    // velocity -= velocity_offset;

    // Get current color
    vec3 curr_m = texelFetch(ShadedScene, coord, 0).xyz;

    vec2 last_coord = texcoord + velocity;
    if (!in_unit_rect(last_coord)) {
        // We don't have any data for the last frame. We have to fallback to our
        // current color.
        result = curr_m;
        return; 
    }

    // Find the AABB of our direct neighbours
    vec3 aabb_min = vec3(1e10);
    vec3 aabb_max = vec3(-1e10);
    vec3 aabb_center = vec3(0);
    int num_samples = 0;
    for (int x = -1; x <= 1; ++x) {
        for (int y = -1; y <= 1; ++y) {
            // if (abs(x) + abs(y) > 1)
            //     continue;
            vec3 color = texelFetch(ShadedScene, coord + ivec2(x, y), 0).xyz;
            color = rgb_to_ycgco(color);
            aabb_min = min(aabb_min, color);
            aabb_max = max(aabb_max, color);
            aabb_center += color;
            num_samples += 1;
        }
    }

    aabb_center /= float(num_samples);

    vec2 one_pixel = 1.0 / SCREEN_SIZE;
    const float bbs = 1.0;

    // Get last frame texels
    float blend_weight = 1.0;
    vec3 last_m = textureLod(Previous_TemporalAAPostResolve,  last_coord, 0).xyz;
    vec3 last_tl = textureLod(Previous_TemporalAAPostResolve, last_coord + vec2(-bbs, -bbs) * one_pixel, 0).xyz;
    vec3 last_tr = textureLod(Previous_TemporalAAPostResolve, last_coord + vec2(bbs, -bbs) * one_pixel, 0).xyz;
    vec3 last_bl = textureLod(Previous_TemporalAAPostResolve, last_coord + vec2(-bbs, bbs) * one_pixel, 0).xyz;
    vec3 last_br = textureLod(Previous_TemporalAAPostResolve, last_coord + vec2(bbs, bbs) * one_pixel, 0).xyz;

    last_m = rgb_to_ycgco(last_m);
    // last_m = clamp(last_m, aabb_min, aabb_max);
    last_m = clip_aabb_v3(aabb_min, aabb_max, aabb_center, last_m);
    last_m = ycgco_to_rgb(last_m);


    float neighbor_diff = length(clamp(last_tl, aabb_min, aabb_max) - last_tl)
                        + length(clamp(last_tr, aabb_min, aabb_max) - last_tr)
                        + length(clamp(last_bl, aabb_min, aabb_max) - last_bl)
                        + length(clamp(last_br, aabb_min, aabb_max) - last_br);

    float max_difference = clamp(max(
        get_luminance(last_m),
        get_luminance(curr_m)), 0.0001, 15.0) * RS_MAX_CLIP_DIST;

    // For moving objects, decrease maximum tolerance
    float motion_factor = saturate(length(velocity) * WINDOW_HEIGHT / 2.0);

    // max_difference *= motion_factor;

    // if (neighbor_diff >= max_difference)
    //     blend_weight = 0.0;

    float blend_amount = saturate(distance(last_m.xyz, curr_m.xyz) * RS_DISTANCE_SCALE);

    // Merge the sample with the current color, in case we can't pick it
    last_m = mix(curr_m, last_m, blend_weight);

    float weight = saturate(1.0 /
        mix(RS_KEEP_GOOD_DURATION, RS_KEEP_BAD_DURATION, blend_amount));

    weight = mix(weight, 1.0, motion_factor * 0.5);    

    result = max(vec3(0.0), mix(last_m, curr_m, weight));

}
