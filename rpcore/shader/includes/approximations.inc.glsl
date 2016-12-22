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

 /*
Approximations

The idea of this file is that all approximations are contained
here, and the rest of the render pipeline is physically (almost) correct, or
at least physically based.

 */


float approx_sphere_light_specular_energy(float roughness, float sphere_radius, float d_sq) {
    float f = 1.0;

    // Smaller lights emit less energy, we have to convert from lumens here
    f *= sphere_radius * sphere_radius;

    // Light size decreases quadradically by distance
    f *= 1.0 / max(0.01, d_sq);

    // Prevent super bright highlights on small roughness values
    f *= roughness * roughness * 70;
    f *= max(0.02, (1 - roughness) * (1 - roughness));

    f *= ONE_BY_PI;

    return f;
}

float approx_spot_light_specular_energy(float roughness, float cos_fov) {
    return 1.0 / 100.0;
}


float approx_tube_light_specular_energy(float roughness, float tube_length, float tube_radius, float d_sq) {
    float r = roughness * roughness;
    float inv_r = (1 - roughness) * (1 - roughness);
    r *= inv_r * inv_r * inv_r;
    return 35.0 * r / (d_sq);
}

float approx_tube_light_diff_energy(float tube_radius, float tube_length) {
    return 1.0 / 50.0;
}


vec3 approx_merge_clearcoat_specular(vec3 specular, vec3 specular_coat, float LxH) {
    // http://www.cescg.org/CESCG-2010/papers/ElekOskar.pdf
    float f0 = CLEARCOAT_SPECULAR;
    float approx_fresnel = pow(saturate(LxH), 5.0);
    float fresnel = f0 + (1 - f0) * approx_fresnel;

    float transmittance = 1.0 - fresnel;
    vec3 result = specular_coat * fresnel;
    result += specular * transmittance;
    return result;
}


// Computes the angle-based attenuation for a spot light
float approx_spotlight_attenuation(vec3 l, vec3 spot_dir, float fov, out float linear_angle) {

    float cos_angle = dot(l, -spot_dir);

    // Rescale angle to fit the full range of the IES profile. We only do this
    // for spot lights, for sphere lights we use the actual angle.
    // This is NOT physically correct for spotlights without a FoV of 180deg.
    // However, IES profiles might look quite boring when not getting rescaled,
    // so the rescaling is performed.
    linear_angle = (cos_angle - fov) / (1 - fov);
    float angle_att = saturate(linear_angle);


    // XXX: Mitsuba computes attenuation differently. But this fits
    // much better, even if not entirely physically correct.
    return angle_att * angle_att * 0.25;
}


// Transforms the roughness for clearcoat layers, this is because rays are
// scattered differently
float approx_clearcoat_roughness_transform(float roughness) {
    return roughness * 1.0;
}

vec3 approx_metallic_fresnel(Material m, float NxV) {
    return vec3(m.basecolor);
    vec3 metallic_energy_f0 = vec3(1.0 - 0.7 * m.roughness) * m.basecolor;
    vec3 metallic_energy_f90 = mix(vec3(1), 0.5 * m.basecolor, m.linear_roughness);
    vec3 metallic_fresnel = mix(metallic_energy_f0, metallic_energy_f90,
        pow(1 - NxV, 3.6 - 2.6 * m.linear_roughness));
    return vec3(metallic_fresnel);
}


vec3 approx_glass_multiplier(vec3 color, float fresnel, float roughness) {
    return color * (1 + 2 * fresnel * (1 - roughness));
}