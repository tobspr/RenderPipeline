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
#pragma include "includes/pbr_reference_lighting.inc.glsl"
#pragma include "includes/LTC.inc.glsl"
#pragma include "includes/approximations.inc.glsl"

// Closest point on spherical area light
vec3 get_spherical_area_light_vector(vec3 n, vec3 l_unscaled, vec3 v, float sphere_radius) {
    vec3 r = reflect(-v, n);
    vec3 center_to_ray = dot(l_unscaled, r) * r - l_unscaled;
    vec3 closest_point = l_unscaled + center_to_ray * 
        saturate(sphere_radius / max(1e-6, length(center_to_ray)));
    return closest_point;
}


vec3 process_spotlight(Material m, LightData light, vec3 v, float shadow) {
    return vec3(0);
}

float light_clip_fallof(LightData light, vec3 pos) {

    float d = distance(pos, get_light_position(light));
    float max_d = get_max_cull_distance(light);
    // Falloff has the following characteristics
    // f(0.8)  = 1
    // f(1)    = 0
    // f'(0.8) = 1
    // f'(1)   = 0
    // f(x) := (1 - max(0.0, min(1.0, (x - 0.8) / 0.2)) ^ 5) ^ 5;
    // float falloff = pow(1.0 - pow(saturate((d / max_d - 0.8) / 0.2), 5.0), 5.0);
    float falloff = pow(1.0 - pow(saturate((d / max_d - 0.8) / 0.2), 5.0), 5.0);
    return falloff;
}

vec3 process_spherelight(Material m, LightData light, vec3 v, float shadow) {
    #if SPECIAL_MODE_ACTIVE(GROUND_TRUTH)
        return process_spherelight_reference(m, light, v, shadow);
    #endif

    vec3 light_pos = get_light_position(light);
    float sphere_radius = get_spherelight_sphere_radius(light);

    float NxV = saturate(dot(m.normal, v));
    vec3 l_unscaled = light_pos - m.position;

    vec3 accum = vec3(0);
    vec3 f0 = get_material_f0(m);
    {

        // Specular
        vec3 l_unscaled_spec = get_spherical_area_light_vector(m.normal, l_unscaled, v, sphere_radius);
        // vec3 l_unscaled_spec = l_unscaled;

        vec3 l = normalize(l_unscaled_spec);
        vec3 h = normalize(l + v);

        float NxH = saturate(dot(m.normal, h));
        float NxL = saturate(dot(m.normal, l));
        float LxH = saturate(dot(l, h));

        float D = brdf_distribution(NxH, m.roughness);
        vec3 F = brdf_schlick_fresnel(f0, LxH);
        float G = brdf_visibility_neumann(NxV, NxL);

        accum += brdf_cook_torrance(D, G, F, NxV, NxL) *
            approx_sphere_light_specular_energy(m.roughness, sphere_radius, dot(l_unscaled_spec, l_unscaled_spec));        
    }

    {
        // Diffuse
        vec3 l = normalize(l_unscaled);
        float att = 1.0 / max(0.01, dot(l_unscaled, l_unscaled));
        float NxL = saturate(dot(m.normal, l));

        // Luminous power -> luminance
        // XXX: Missing division by 4 * pi^2 here though. But matches mitsuba well. hm. 
        float scale_factor = sphere_radius * sphere_radius;
        accum += att * NxL * get_material_diffuse(m) * scale_factor;
    }

    accum *= shadow;
    accum *= get_light_color(light);
    accum *= light_clip_fallof(light, m.position);
    return accum;
}


vec3 process_rectanglelight(Material m, LightData light, vec3 v, float shadow) {

    vec3 light_pos = get_light_position(light);
    vec3 up_vector = get_rectangle_upvector(light);
    vec3 right_vector = -get_rectangle_rightvector(light);

    vec3 points[4];
    points[0] = light_pos - right_vector - up_vector;
    points[1] = light_pos + right_vector - up_vector;
    points[2] = light_pos + right_vector + up_vector;
    points[3] = light_pos - right_vector + up_vector;

    vec2 coords = LTC_Coords(dot(m.normal, v), m.roughness);
    mat3 minv = LTC_Matrix(LTCMatTex, coords);
    vec3 specular = LTC_Evaluate(m.normal, v, m.position, minv, points, false);    
    vec3 diffuse = LTC_Evaluate(m.normal, v, m.position, mat3(1), points, false);    

    vec3 f0 = get_material_f0(m);

    vec2 schlick = textureLod(LTCAmpTex, coords, 0).xy;
    specular *= f0 * schlick.x + (1.0 - f0) * schlick.y;
    specular;

    diffuse *= get_material_diffuse(m);
    return (diffuse + specular) * get_light_color(light) * (light_clip_fallof(light, m.position) * shadow / TWO_PI);
}
