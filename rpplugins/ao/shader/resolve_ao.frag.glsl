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

#define USE_GBUFFER_EXTENSIONS
#pragma include "includes/gbuffer.inc.glsl"
#pragma include "includes/normal_packing.inc.glsl"
#pragma include "includes/transforms.inc.glsl"

uniform sampler2D CurrentTex;
uniform sampler2D CombinedVelocity;
uniform sampler2D Previous_ResolvedAO;
uniform sampler2D Previous_SceneDepth;

out vec2 result;

void main() {
    ivec2 coord = ivec2(gl_FragCoord.xy);

    float curr_depth = get_depth_at(coord * 2);
    vec2 velocity = texelFetch(CombinedVelocity, coord * 2, 0).xy;

    vec2 curr_coord = get_half_native_texcoord();
    vec2 last_native_coord = get_half_native_texcoord() + velocity;
    vec2 last_coord = get_half_texcoord() + velocity;

    // XXX: use truncate coordinate maybe
    vec2 last_data = textureLod(Previous_ResolvedAO, last_native_coord, 0).xy;
    float last_depth = textureLod(Previous_SceneDepth, last_coord, 0).x;

    vec2 curr_ao = textureLod(CurrentTex, curr_coord, 0).xy;

    #if 0
        result = texelFetch(CurrentTex, coord, 0).xy;
        return;
    #endif

    vec3 last_pos = calculate_surface_pos(last_depth, vec2(last_native_coord), MainSceneData.last_inv_view_proj_mat_no_jitter);
    vec3 curr_pos = calculate_surface_pos(curr_depth, vec2(curr_coord), MainSceneData.inv_view_proj_mat_no_jitter);

    const float max_dist = GET_SETTING(ao, max_resolve_dist);
    float distance_factor = step(max_dist * max_dist, distance_squared(last_pos, curr_pos));

    float weight = mix(1 - 1.0 / 9.0, 0.0, distance_factor);

    if (!in_unit_rect(last_coord)) {
        weight = 0.0;
    }

    result.xy = mix(curr_ao, last_data.xy, weight);

}
