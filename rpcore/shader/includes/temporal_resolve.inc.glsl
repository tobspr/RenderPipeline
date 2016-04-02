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

#pragma once

#define USE_GBUFFER_EXTENSIONS
#pragma include "includes/color_spaces.inc.glsl"
#pragma include "includes/transforms.inc.glsl"
#pragma include "includes/gbuffer.inc.glsl"

// Maximum color distance
#ifndef RS_MAX_CLIP_DIST
   #define RS_MAX_CLIP_DIST 0.5
#endif

// Blending factor
#ifndef RS_DISTANCE_SCALE
   #define RS_DISTANCE_SCALE 10.0
#endif

// How long to keep good pixels
#ifndef RS_KEEP_GOOD_DURATION
   #define RS_KEEP_GOOD_DURATION 10.0
#endif

// How long to keep bad pixels
#ifndef RS_KEEP_BAD_DURATION
   #define RS_KEEP_BAD_DURATION 3.0
 #endif

#ifndef RS_AABB_SIZE
    #define RS_AABB_SIZE 1.0
#endif

/*

Uses the reprojection suggested in:
http://www.crytek.com/download/Sousa_Graphics_Gems_CryENGINE3.pdf

*/
vec4 resolve_temporal(sampler2D current_tex, sampler2D last_tex, vec2 curr_coord, vec2 last_coord) {
    vec2 one_pixel = 1.0 / SCREEN_SIZE;
    vec4 curr_m    = texture(current_tex, curr_coord);

    // Out of screen, can early out
    if (out_of_screen(last_coord)) {
        return max(vec4(0.0), curr_m);
    }

    // Bounding box size
    const float bbs = RS_AABB_SIZE;

    // Get current frame neighbor texels
    vec4 curr_tl = texture(current_tex, curr_coord + vec2(-bbs, -bbs) * one_pixel);
    vec4 curr_tr = texture(current_tex, curr_coord + vec2( bbs, -bbs) * one_pixel);
    vec4 curr_bl = texture(current_tex, curr_coord + vec2(-bbs,  bbs) * one_pixel);
    vec4 curr_br = texture(current_tex, curr_coord + vec2( bbs,  bbs) * one_pixel);

    // Get current frame neighbor AABB
    vec4 curr_min = min5(curr_m, curr_tl, curr_tr, curr_bl, curr_br);
    vec4 curr_max = max5(curr_m, curr_tl, curr_tr, curr_bl, curr_br);

    // TODO: Use velocity of closest depth fragment

    // Get last frame texels
    float blend_weight = 1.0;
    vec4 last_m  = texture(last_tex, last_coord);
    vec4 last_tl = texture(last_tex, last_coord + vec2(-bbs, -bbs) * one_pixel);
    vec4 last_tr = texture(last_tex, last_coord + vec2( bbs, -bbs) * one_pixel);
    vec4 last_bl = texture(last_tex, last_coord + vec2(-bbs,  bbs) * one_pixel);
    vec4 last_br = texture(last_tex, last_coord + vec2( bbs,  bbs) * one_pixel);

    float neighbor_diff = length(clamp(last_tl.xyz, curr_min.xyz, curr_max.xyz) - last_tl.xyz)
                        + length(clamp(last_tr.xyz, curr_min.xyz, curr_max.xyz) - last_tr.xyz)
                        + length(clamp(last_bl.xyz, curr_min.xyz, curr_max.xyz) - last_bl.xyz)
                        + length(clamp(last_br.xyz, curr_min.xyz, curr_max.xyz) - last_br.xyz);

    float max_difference = clamp( max(get_luminance(last_m.xyz), get_luminance(curr_m.xyz)), 0.0001, 15.0) * RS_MAX_CLIP_DIST;

    if (neighbor_diff >= max_difference)
        blend_weight = 0.0;

    float blend_amount = saturate(distance(last_m.xyz, curr_m.xyz) * RS_DISTANCE_SCALE );

    // Merge the sample with the current color, in case we can't pick it
    last_m = mix(curr_m, last_m, blend_weight);
    float weight = saturate(1.0 / mix(RS_KEEP_GOOD_DURATION, RS_KEEP_BAD_DURATION, blend_amount));
    
    return max(vec4(0.0), mix(last_m, curr_m, weight));
}
