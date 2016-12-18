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
#pragma include "includes/brdf.inc.glsl"
#pragma include "includes/ies_lighting.inc.glsl"

// Computes the quadratic attenuation curve
float light_clip_fade(float dist_square, float max_distance) {
    #if 0
        return step(dist_square, max_distance * max_distance);
    #endif

    #if 1
        // Fade out at the border to avoid culling issues
        const float falloff = 0.2;
        float linear_dist = 1 - dist_square / (max_distance * max_distance);
        return sqrt(saturate(linear_dist / falloff));

    #endif
}


// Computes the attenuation for a spot light
float get_spotlight_attenuation(vec3 l, vec3 light_dir, float fov,
        float dist_sq, int ies_profile) {
    float dist_attenuation = 1.0;
    float cos_angle = dot(l, -light_dir);
    dist_attenuation *= 1.0 / dist_sq;

    // Rescale angle to fit the full range of the IES profile. We only do this
    // for spot lights, for sphere lights we use the actual angle.
    // This is NOT physically correct for spotlights without a FoV of 180deg.
    // However, IES profiles might look quite boring when not getting rescaled,
    // so the rescaling is performed. 
    float linear_angle = (cos_angle - fov) / (1 - fov);
    float angle_att = saturate(linear_angle);
    float ies_factor = get_ies_factor(ies_profile, linear_angle, 0);
    return ies_factor * angle_att * dist_attenuation;
}


// Closest point on spherical area light
vec3 get_spherical_area_light_vector(vec3 n, vec3 l_unscaled, vec3 v, float sphere_radius) {
    vec3 r = reflect(-v, n);
    vec3 center_to_ray = dot(l_unscaled, r) * r - l_unscaled;
    vec3 closest_point = l_unscaled + center_to_ray *
        saturate(sphere_radius / max(1e-6, length(center_to_ray)));
    return closest_point;
}


vec3 get_spherical_area_light_horizon(vec3 l_unscaled, vec3 n, float radius) {
    return normalize(l_unscaled + n * (0.5 * radius));
} 

vec2 get_spherelight_energy(float alpha, float sphere_radius, float d) {

    // XXX: Should subtract sphere_radius from d, but without it matches mitsuba better
    float diff_energy = 0.15 / max(0.001, pow(max(0, d), 2.2) + sphere_radius);
    // diff_energy *= 0;

    // Fade out on high roughness
    const float fade_factor = 0.95;
    // float alpha1 = max(0.2, fade_factor - alpha) / fade_factor;
    float alpha1 = 1;

    // float roughness_factor = pow(alpha, 1.6) * alpha1;
    float roughness_factor = alpha * alpha * alpha1;
    float spec_energy = roughness_factor / max(0.1, pow(sphere_radius, 1.5)); // approximation
    spec_energy *= 0.13 / max(1.0, d);


    return vec2(diff_energy, spec_energy);
}


vec3 shading_core(Material m, float NxV, float NxL, float LxH, float VxH, float NxH, float attenuation, vec2 energy, vec2 clearcoat_energy) {

    vec3 f0 = get_material_f0(m);
    
    // Diffuse contribution
    vec3 shading_result = brdf_diffuse(NxV, NxL, LxH, VxH, m.roughness)
                            * m.basecolor * (1 - m.metallic) * NxL * energy.x * attenuation;

    // Specular contribution:
    // We add some roughness for clearcoat - this is due to the reason that
    // light gets scattered and thus a wider highlight is shown.
    // This approximates the reference in mitsuba very well.
    // float distribution = brdf_distribution(NxH, m.roughness);
    float distribution = brdf_distribution(NxH, m.roughness); // xxx
    float visibility = brdf_visibility(NxL, NxV, NxH, VxH, m.roughness);
    // vec3 fresnel = brdf_schlick_fresnel(f0, LxH);
    vec3 fresnel = brdf_schlick_fresnel_combined(f0, LxH, m.metallic);

    float mm = mix(M_PI * NxV * square(1 - m.roughness), 2.0, m.metallic); // we need this to match mitsuba ... but why?!
    
    shading_result += (distribution * visibility) * fresnel / (4.0 * NxV * NxL) * energy.y * mm;
    // shading_result += (distribution * visibility) * fresnel * energy.y * mm;
    
    #if 1
    if (m.shading_model == SHADING_MODEL_CLEARCOAT) {
        float distribution_coat = brdf_distribution(NxH, CLEARCOAT_ROUGHNESS);
        float visibility_coat = brdf_visibility(NxL, NxV, NxH, VxH, CLEARCOAT_ROUGHNESS);
        vec3 fresnel_coat = brdf_schlick_fresnel(vec3(CLEARCOAT_SPECULAR), LxH);

        // Approximation to match reference
        // shading_result *= (1 - fresnel_coat.x);

        float f = 0.2 + 0.8 * pow(1 - NxV, 3.0);
        // float f = pow(NxV;
        // shading_result *= 0.4 + 3.0 * m.linear_roughness;
        // shading_result *= 0.5 + 0.5 * m.basecolor;
        // shading_result *= NxV * NxH * NxH * 1.5;
        shading_result *= 1.5;

        vec3 coat_spec = (distribution_coat * visibility_coat) * fresnel_coat / (4.0 * NxV * NxL) * clearcoat_energy.y;
        // shading_result += coat_spec * 0.2;
        coat_spec *= 2;
        shading_result = mix(shading_result, coat_spec, f);
    }
    #endif

    return shading_result;
}

// Computes a lights influence
// TODO: Make this method faster
vec3 apply_light(Material m, vec3 v, vec3 l, vec3 light_color, float attenuation, float shadow,
    vec3 transmittance, vec2 energy, vec2 clearcoat_energy, vec3 l_diffuse) {

    #if 0
        // Debugging: Fast rendering path
        return light_color * attenuation * energy.x;
    #endif

    // XXX
    l_diffuse = normalize(l_diffuse);
    l = normalize(l);
    v = normalize(v);
    // m.normal = normalize(m.normal);

    float NxL = saturate(dot(m.normal, l_diffuse));

    if (m.shading_model == SHADING_MODEL_FOLIAGE) {
        transmittance = transmittance.xxx;
    } else if (m.shading_model == SHADING_MODEL_SKIN) {
        NxL = saturate(0.3 + dot(m.normal, l_diffuse));
    } else {
        transmittance = vec3(1);
    }

    // Compute the dot products
    vec3 h = normalize(l + v);
    float NxV = max(1e-5, dot(m.normal, v));
    float NxH = max(1e-5, dot(m.normal, h));
    float VxH = clamp(dot(v, h), 1e-5, 1.0);
    float LxH = max(0, dot(l, h));

    vec3 shading_result = shading_core(m, NxV, NxL, LxH, VxH, NxH, attenuation, energy, clearcoat_energy);

    return max(vec3(0), (shading_result * light_color) * (shadow * NxL) * transmittance);
}

vec3 apply_light(Material m, vec3 v, vec3 l, vec3 light_color, float attenuation,
        float shadow, vec3 transmittance) {
    return apply_light(
        m, v, l, light_color, attenuation, shadow, transmittance, vec2(1.0), vec2(1.0), l);
}
