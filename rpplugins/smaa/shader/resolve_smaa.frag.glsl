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
#define RS_KEEP_GOOD_DURATION float(GET_SETTING(smaa, history_length))
#define RS_KEEP_BAD_DURATION (RS_KEEP_GOOD_DURATION * 0.5)

#pragma include "includes/temporal_resolve.inc.glsl"
#pragma include "includes/color_spaces.inc.glsl"

uniform sampler2D CurrentTex;
uniform sampler2D Previous_SMAAPostResolve;
uniform sampler2D CombinedVelocity;

uniform int jitterIndex;

out vec3 result;



vec3 clip_aabb_v3(vec3 aabb_min, vec3 aabb_max, vec3 p, vec3 q)
{
    // note: only clips towards aabb center (but fast!)
    vec3 p_clip = 0.5 * (aabb_max + aabb_min);
    vec3 e_clip = 0.5 * (aabb_max - aabb_min);

    vec3 v_clip = q - p_clip;
    vec3 v_unit = v_clip / e_clip;
    vec3 a_unit = abs(v_unit);
    float ma_unit = max3(a_unit.x, a_unit.y, a_unit.z);

    if (ma_unit > 1.0)
        return p_clip + v_clip / ma_unit;
    else
        return q; // point inside aabb
}

void main() {
    ivec2 coord = ivec2(gl_FragCoord.xy);
    vec2 texcoord = get_texcoord();

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
    vec3 curr_m = texelFetch(CurrentTex, coord, 0).xyz;

    vec2 last_coord = texcoord + velocity;
    if (!in_unit_rect(last_coord)) {
        // We don't have any data for the last frame. We have to fallback to our
        // current color.
        result = curr_m;
        return; 
    }

    // Find the AABB of our direct neighbours
    vec3 aabb_min = vec3(1);
    vec3 aabb_max = vec3(0);
    for (int x = -1; x <= 1; ++x) {
        for (int y = -1; y <= 1; ++y) {
            vec3 color = texelFetch(CurrentTex, coord + ivec2(x, y), 0).xyz;
            aabb_min = min(aabb_min, color);
            aabb_max = max(aabb_max, color);
        }
    }

    vec2 one_pixel = 1.0 / SCREEN_SIZE;
    const float bbs = 1.0;

    // Get last frame texels
    float blend_weight = 1.0;
    vec3 last_m = textureLod(Previous_SMAAPostResolve,  last_coord, 0).xyz;
    vec3 last_tl = textureLod(Previous_SMAAPostResolve, last_coord + vec2(-bbs, -bbs) * one_pixel, 0).xyz;
    vec3 last_tr = textureLod(Previous_SMAAPostResolve, last_coord + vec2(bbs, -bbs) * one_pixel, 0).xyz;
    vec3 last_bl = textureLod(Previous_SMAAPostResolve, last_coord + vec2(-bbs, bbs) * one_pixel, 0).xyz;
    vec3 last_br = textureLod(Previous_SMAAPostResolve, last_coord + vec2(bbs, bbs) * one_pixel, 0).xyz;

    float neighbor_diff = length(clamp(last_tl, aabb_min, aabb_max) - last_tl)
                        + length(clamp(last_tr, aabb_min, aabb_max) - last_tr)
                        + length(clamp(last_bl, aabb_min, aabb_max) - last_bl)
                        + length(clamp(last_br, aabb_min, aabb_max) - last_br);

    float max_difference = clamp(max(
        get_luminance(last_m),
        get_luminance(curr_m)), 0.0001, 15.0) * RS_MAX_CLIP_DIST;

    // For moving objects, decrease maximum tolerance
    float motion_factor = mix(1.0, 0.01, saturate(length(velocity) * WINDOW_HEIGHT / 4.0));

    max_difference *= motion_factor;

    if (neighbor_diff >= max_difference)
        blend_weight = 0.0;

    float blend_amount = saturate(distance(last_m.xyz, curr_m.xyz) * RS_DISTANCE_SCALE) * motion_factor;

    // Merge the sample with the current color, in case we can't pick it
    last_m = mix(curr_m, last_m, blend_weight);

    float weight = saturate(1.0 /
        mix(RS_KEEP_GOOD_DURATION, RS_KEEP_BAD_DURATION, blend_amount));

    result = max(vec3(0.0), mix(last_m, curr_m, weight));

}
