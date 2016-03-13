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

#pragma include "includes/material.struct.glsl"
#pragma include "includes/brdf.inc.glsl"
#pragma include "includes/ies_lighting.inc.glsl"

// Computes the quadratic attenuation curve
float attenuation_curve(float dist_sq, float radius) {
    #if 0
        return step(dist_sq, radius * radius);
    #endif

    #if 1
        float r_sq = radius * radius;
        float f = saturate(1.0 - (dist_sq * dist_sq) / (r_sq * r_sq));
        return f * f / (1e-3 + dist_sq);
    #endif
}

// Computes the attenuation for a point light
float get_pointlight_attenuation(vec3 l, float radius, float dist_sq, int ies_profile) {
    return attenuation_curve(dist_sq, radius) * get_ies_factor(-l, ies_profile);
}

// Computes the attenuation for a spot light
float get_spotlight_attenuation(vec3 l, vec3 light_dir, float fov, float radius, float dist_sq, int ies_profile) {
    float dist_attenuation = attenuation_curve(dist_sq, radius);
    float cos_angle = dot(l, -light_dir);

    // Rescale angle to fit the full range. We only do this for spot lights,
    // for point lights we use the actual angle
    float linear_angle = (cos_angle - fov) / (1 - fov);
    float angle_att = saturate(linear_angle);
    float ies_factor = get_ies_factor(ies_profile, linear_angle, 0);
    return ies_factor * angle_att * angle_att * dist_attenuation;
}


// Computes a lights influence
// @TODO: Make this method faster
vec3 apply_light(Material m, vec3 v, vec3 l, vec3 light_color, float attenuation, float shadow, vec3 transmittance) {

    // Debugging: Fast rendering path
    #if 0
        return max(0, dot(m.normal, l)) * light_color * attenuation * m.basecolor * shadow;
    #endif

    float NxL = 0.0;

    if (m.shading_model == SHADING_MODEL_FOLIAGE) {
        NxL = saturate(0.9 + max(0, dot(m.normal, l)));
        transmittance = transmittance.xxx;
        // transmittance = vec3(1);
    } else if (m.shading_model == SHADING_MODEL_SKIN) {
        NxL = saturate(0.3 + dot(m.normal, l));
    } else {
        transmittance = vec3(1);
        NxL = saturate(dot(m.normal, l));
    }


    // Compute the dot product
    vec3 h = normalize(l + v);
    float NxV = max(1e-5, dot(m.normal, v));
    float NxH = max(0.0, dot(m.normal, h));
    float VxH = clamp(dot(v, h), 1e-5, 1.0);
    float LxH = max(0, dot(l, h));

    vec3 f0 = get_material_f0(m);

    // Diffuse contribution
    vec3 shading_result = brdf_diffuse(NxV, LxH, m.roughness) * m.basecolor * (1 - m.metallic);

    // Specular contribution
    // float distribution = brdf_distribution(NxH, m.roughness);
    float distribution = brdf_distribution(NxH, m.roughness);
    float visibility = brdf_visibility(NxL, NxV, NxH, VxH, m.roughness);
    vec3 fresnel = mix(f0, vec3(1), brdf_schlick_fresnel(f0, LxH));
    // vec3 fresnel = f0;

    // The division by 4 * NxV * NxL is done in the geometric (visibility) term
    // already, so to evaluate the complete brdf we just do a multiply
    shading_result += (distribution * visibility) * fresnel;

    if(m.shading_model == SHADING_MODEL_CLEARCOAT) {
        float distribution_coat = brdf_distribution(NxH, CLEARCOAT_ROUGHNESS);
        float visibility_coat = brdf_visibility(NxL, NxV, NxH, VxH, CLEARCOAT_ROUGHNESS);
        vec3 fresnel_coat = brdf_schlick_fresnel(vec3(CLEARCOAT_SPECULAR), LxH);
        shading_result *= 1 - fresnel_coat;
        shading_result += (distribution_coat * visibility_coat) * fresnel_coat;

    }

    return (shading_result * light_color) * (attenuation * shadow * NxL) * transmittance;
}
