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

#pragma include "includes/material.inc.glsl"
#pragma include "includes/normal_packing.inc.glsl"
#pragma include "includes/brdf.inc.glsl"

/*

GBuffer Packing

*/

layout(location = 0) out vec4 gbuffer_out_0;
layout(location = 1) out vec4 gbuffer_out_1;
layout(location = 2) out vec4 gbuffer_out_2;

vec2 compute_velocity() {
    // Compute velocity based on this and last frames mvp matrix
    vec4 last_proj_pos = vOutput.last_proj_position;
    vec2 last_texcoord = fma(last_proj_pos.xy / last_proj_pos.w, vec2(0.5), vec2(0.5));
    vec2 curr_texcoord = gl_FragCoord.xy / SCREEN_SIZE;
    return (curr_texcoord - last_texcoord);
}

// Lean mapping
float adjust_roughness(float roughness, float avg_normal_length) {
    // Based on The Order : 1886 SIGGRAPH course notes implementation
    if (avg_normal_length < 1.0)
    {
        float avg_len_sq = avg_normal_length * avg_normal_length;
        float kappa = (3 * avg_normal_length - avg_normal_length * avg_len_sq) /
            (1 - avg_len_sq);
        float variance = 1.0 / (2.0 * kappa) ;
        return sqrt(roughness * roughness + variance);
    }
    return roughness;
}


void render_material(MaterialShaderOutput m) {

    // Compute material properties
    vec3 normal = normalize(m.normal);
    vec2 packed_normal = pack_normal_octahedron(normal);
    vec2 velocity = compute_velocity();

    // Clamp BaseColor, but only for negative values, we allow values > 1.0
    // vec3 basecolor = pow(max(vec3(0), m.basecolor), vec3(2.2)) * 1.0;
    vec3 basecolor = max(vec3(0), m.basecolor);

    // Clamp properties like specular and metallic, which have to be in the
    // 0 ... 1 range
    float specular = clamp(m.specular_ior, 1.0001, 2.51);
    float metallic = saturate(m.metallic);

    if (m.shading_model == SHADING_MODEL_CLEARCOAT) {
        // Scale up roughness since the layer refracts the rays (this is an approximation)
        m.roughness *= 1.4;
    }

    float roughness = clamp(m.roughness, MINIMUM_ROUGHNESS, 1.0);

    #if !REFERENCE_MODE
        roughness = adjust_roughness(roughness, length(m.normal));
    #endif

    // Pack all values to the gbuffer
    gbuffer_out_0 = vec4(basecolor.r, basecolor.g, basecolor.b, roughness);
    gbuffer_out_1 = vec4(packed_normal.x, packed_normal.y, metallic, specular);
    gbuffer_out_2 = vec4(velocity.x, velocity.y, m.shading_model, m.shading_model_param0);
}
