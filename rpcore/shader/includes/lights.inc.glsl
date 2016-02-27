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
float attenuation_curve(float dist, float radius) {
    #if 0
        return step(dist, radius);
    #endif

    #if 1
        // We do a inverse square falloff, however we weight it by a
        // linear attenuation to make it go to zero at the lights radius.
        // This is because the culling needs a fixed radius. I like the linear
        // attenuation weight more than using an additional fallof starting at
        // 80% or so.
        float lin_att = 1.0 - saturate(dist / radius);
        float d_by_r = dist / radius;
        return lin_att / max(0.001, d_by_r * d_by_r + 1);
    #endif
}

// Computes the attenuation for a point light
float get_pointlight_attenuation(vec3 l, float radius, float dist, int ies_profile) {
    float attenuation = attenuation_curve(dist, radius);
    return attenuation * get_ies_factor(l, ies_profile);
}

// Computes the attenuation for a spot light
float get_spotlight_attenuation(vec3 l, vec3 light_dir, float fov, float radius, float dist, int ies_profile) {
    float dist_attenuation = attenuation_curve(dist, radius);
    float cos_angle = dot(l, -light_dir);

    // Rescale angle to fit the full range. We only do this for spot lights,
    // for point lights we use the actual angle
    float linear_angle = (cos_angle - fov) / (1 - fov);
    float angle_att = attenuation_curve(1 - linear_angle, 1.0);
    float ies_factor = get_ies_factor(ies_profile, linear_angle, 0);
    return ies_factor * angle_att * dist_attenuation;
}


// Computes a lights influence
// @TODO: Make this method faster
vec3 apply_light(Material m, vec3 v, vec3 l, vec3 light_color, float attenuation, float shadow, vec4 directional_occlusion, vec3 transmittance) {

    // Debugging: Fast rendering path
    #if 0
        return max(0, dot(m.normal, l)) * light_color * attenuation * m.basecolor * shadow;
    #endif

    // TODO: Check if skipping on low attenuation is faster than just shading
    // without any effect. Would look like this: if(attenuation < epsilon) return vec3(0);

    // Skip shadows, should be faster than evaluating the BRDF on most cards,
    // at least if the shadow distribution is coherent
    // HOWEVER: If we are using translucency, we have to also consider shadowed
    // areas. So for now, this is disabled. If we reenable it, we probably should
    // also check if translucency is greater than a given epsilon.
    // if (shadow < 0.001)
        // return vec3(0);

    // Weight transmittance by the translucency factor
    transmittance = mix(vec3(1), transmittance, m.translucency);

    // Translucent objects don't recieve shadows, this just makes them look weird.
    shadow = mix(shadow, 1, saturate(m.translucency));

    // Compute the dot product, for translucent materials we also add a bias
    vec3 h = normalize(l + v);
    float NxL = saturate(10.0 * m.translucency + dot(m.normal, l));
    float NxV = max(1e-5, dot(m.normal, v));
    float NxH = max(0.0, dot(m.normal, h));
    float VxH = clamp(dot(v, h), 1e-5, 1.0);
    float LxH = max(0, dot(l, h));


    // Diffuse contribution
    vec3 shading_result = brdf_diffuse(NxV, LxH, m.roughness) * m.basecolor * (1 - m.metallic);

    // Specular contribution
    float distribution = brdf_distribution(NxH, m.roughness);
    float visibility = brdf_visibility(NxL, NxV, NxH, VxH, m.roughness);
    float fresnel = brdf_fresnel(1-LxH, m.roughness);

    // The division by 4 * NxV * NxL is done in the geometric (visibility) term
    // already, so to evaluate the complete brdf we just do a multiply
    shading_result += (distribution * visibility * fresnel) * get_material_f0(m);

    // Special case for directional occlusion and bent normals
    #if IS_SCREEN_SPACE && HAVE_PLUGIN(ao)

        // Compute lighting for bent normal
        float occlusion_factor = saturate(dot(vec4(l, 1.5), directional_occlusion));
        occlusion_factor = pow(occlusion_factor, 3.0);
        shading_result *= occlusion_factor;

    #endif

    return (shading_result * light_color) * (attenuation * shadow * NxL) * transmittance;
}
