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

#version 420

#define USE_MAIN_SCENE_DATA
#pragma include "render_pipeline_base.inc.glsl"
#pragma include "includes/gbuffer.inc.glsl"

#pragma optionNV (unroll all)

uniform GBufferData GBuffer;
uniform sampler2D CurrentTex;
uniform sampler2D LastTex;

out vec3 result;

/*

Uses the reprojection suggested in:
http://www.crytek.com/download/Sousa_Graphics_Gems_CryENGINE3.pdf

*/

// Ray-AABB intersection
float intersect_aabb(vec3 ray_dir, vec3 ray_pos, vec3 box_size)
{
    if (dot(ray_dir, ray_dir) < 1e-10) return 1.0;
    vec3 t1 = (-box_size - ray_pos) / ray_dir;
    vec3 t2 = ( box_size - ray_pos) / ray_dir;
    return max(max(min(t2.x, t1.x), min(t2.y, t1.y)), min(t2.z, t1.z));
}

// Clamps a color to an aabb, returns the weight
float clamp_color_to_aabb(vec3 last_color, vec3 current_color, vec3 min_color, vec3 max_color)
{
    vec3 box_center = 0.5 * (max_color + min_color);
    vec3 box_size = max_color - box_center;
    vec3 ray_dir = current_color - last_color;
    vec3 ray_pos = last_color - box_center;
    return saturate(intersect_aabb(ray_dir, ray_pos, box_size));
}

void main() {
    vec2 texcoord = get_texcoord();
    ivec2 coord = ivec2(gl_FragCoord.xy);

    vec2 velocity = get_gbuffer_velocity(GBuffer, texcoord) / SCREEN_SIZE;
    vec2 old_coord = texcoord - velocity;
    vec3 current_color = textureLod(CurrentTex, texcoord, 0).xyz;
    vec3 last_color = textureLod(LastTex, old_coord, 0).xyz;

    // Out of screen, can early out
    if (old_coord.x < 0.0 || old_coord.x >= 1.0 || old_coord.y < 0.0 || old_coord.y >= 1.0) {
        result = current_color;
        return;
    }

    // Get last frame color AABB
    const int radius = 1;
    vec3 color_min = vec3(1e10);
    vec3 color_max = vec3(0);
    for (int i = -radius; i <= radius; ++i) {
        for (int j = -radius; j <= radius; ++j) {
            vec3 sample_color = texelFetch(CurrentTex, coord + ivec2(i, j), 0).xyz;
            color_min = min(color_min, sample_color);
            color_max = max(color_max, sample_color);
        }
    }

    // Compute weight of the last frames pixel color
    float sample_weight = clamp_color_to_aabb(last_color, current_color, color_min, color_max);
    ivec2 last_coord = ivec2( 0.5 + texcoord * SCREEN_SIZE );
    float neighbor_diff = 0.0;
    for (int i = -radius; i <= radius; ++i) {
        for (int j = -radius; j <= radius; ++j) {
            vec3 sample_color = texelFetch(LastTex, last_coord + ivec2(i, j), 0).xyz;
            neighbor_diff += distance(clamp(sample_color, color_min, color_max), sample_color);
        }
    }

    // Evaluate if we can pickup the sample or not
    if (neighbor_diff < 0.02) sample_weight = 0.0;
    float blend_amount = saturate(distance(last_color, current_color) * 10.0);

    // Merge the sample with the current color, in case we can't pick it
    last_color = mix(last_color, current_color, sample_weight);

    // Compute weight and blend pixels
    float weight = saturate(1.0 / (mix(2.25, 4.5, blend_amount)));
    result = mix(last_color, current_color, weight);
}
