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

 /*
Approximations

The idea of this file is that all approximations are contained
here, and the rest of the render pipeline is physically (almost) correct, or
at least physically based.

 */


float approx_sphere_light_specular_energy(float roughness, float sphere_radius, float d_sq) {
    float r = roughness * roughness;
    float inv_r = (1 - roughness) * (1 - roughness);
    r *= inv_r * inv_r * inv_r;
    return 75.0 * r / (d_sq);
}

float approx_spot_light_specular_energy(float roughness, float cos_fov) {
    return 1.0 / 100.0;
}


// Computes the angle-based attenuation for a spot light
float approx_spotlight_attenuation(vec3 l, vec3 spot_dir, float fov, int ies_profile) {

    float cos_angle = dot(l, -spot_dir);

    // Rescale angle to fit the full range of the IES profile. We only do this
    // for spot lights, for sphere lights we use the actual angle.
    // This is NOT physically correct for spotlights without a FoV of 180deg.
    // However, IES profiles might look quite boring when not getting rescaled,
    // so the rescaling is performed. 
    float linear_angle = (cos_angle - fov) / (1 - fov);
    float angle_att = saturate(linear_angle);
    float ies_factor = get_ies_factor(ies_profile, linear_angle, 0);

    // XXX: Mitsuba computes attenuation differently. But this fits
    // much better, even if not entirely physically correct.
    return ies_factor * angle_att * angle_att * 0.25;
}

