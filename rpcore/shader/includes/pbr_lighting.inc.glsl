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


// Closest point on tube area light
vec3 get_tube_area_light_vector(vec3 n, vec3 light_pos, vec3 pos, vec3 v, float tube_radius,
                                float tube_length, vec3 tube_direction) {
    vec3 R = reflect(-v, n);
    // vec3 center_to_ray = dot(l_unscaled, r) * r - l_unscaled;
    vec3 P0 = light_pos + tube_direction * (0.5 * -tube_length + tube_radius);
    vec3 P1 = light_pos + tube_direction * (0.5 * tube_length - tube_radius);
    vec3 L0 = P0 - pos;
    vec3 L1 = P1 - pos;

    float distL0 = length(L0);
    float distL1 = length(L1);

    vec3 Ld = L1 - L0;
    float RdotL0 = dot(R, L0);
    float RdotLd = dot(R, Ld);
    float L0dotLd = dot(L0, Ld);
    float distLd = length(Ld);
    float t = (RdotL0 * RdotLd - L0dotLd) / (distLd * distLd - RdotLd * RdotLd);

    vec3 closestPoint = L0 + Ld * saturate(t);
    vec3 centerToRay = dot(closestPoint, R) * R - closestPoint;

    // This is where I made the change
    // This is the original line of code from Epic's notes:
    closestPoint = closestPoint + centerToRay * clamp(tube_radius / length(centerToRay), 0.0f, 1.0f);
    // The following line is my version:
    // closestPoint = closestPoint + centerToRay * halfHeight;

    return closestPoint;
}

vec3 get_tube_area_light_diff_vector(vec3 pos, vec3 light_pos, float tube_radius, float tube_length, vec3 tube_direction) {

    // Construct plane with normal of the tube direction, and make it go through the current position
    vec3 plane_nrm = tube_direction;
    vec3 plane_origin = pos;

    vec3 ray_pos = light_pos;
    vec3 ray_dir = normalize(tube_direction);

    float d = dot((plane_origin - ray_pos), plane_nrm) / dot(ray_dir, plane_nrm);

    d = clamp(d, min(0, -tube_length*0.5 + tube_radius), max(0, tube_length*0.5 - tube_radius));

    vec3 l = (light_pos + d * tube_direction) - pos;

    // Take radius into account by shortening the light vector
    #if 0
    float l_len = length(l);
    l /= l_len;
    l *= l_len - tube_radius;
    #endif

    return l;
}


// Makes sure the light influence reaches 0 on culling distance
float light_clip_falloff(LightData light, vec3 pos) {


    float d = distance(pos, get_light_position(light));
    float max_d = get_max_cull_distance(light);

    #if 0
        return step(d, max_d);
    #endif

    // Falloff has the following characteristics
    // f(0.8)  = 1
    // f(1)    = 0
    // f'(0.8) = 1
    // f'(1)   = 0
    // f(x) := (1 - max(0.0, min(1.0, (x - 0.8) / 0.2)) ^ 5) ^ 5;
    float falloff = pow(1.0 - pow(saturate((d / max_d - 0.8) / 0.2), 5.0), 5.0);
    return falloff;
}


vec3 process_spotlight(Material m, LightData light, vec3 v, float shadow) {

    vec3 light_pos = get_light_position(light);
    int ies_profile = get_ies_profile(light);
    vec3 direction = get_spotlight_direction(light);
    float fov = get_spotlight_fov(light);

    vec3 l_unscaled = light_pos - m.position;
    vec3 l = normalize(l_unscaled);

    float light_scale = approx_spotlight_attenuation(l, direction, fov, ies_profile);
    light_scale *= (1 - fov) * M_PI;


    float NxV = saturate(dot(m.normal, v));
    vec3 accum = vec3(0);
    vec3 f0 = get_material_f0(m);

    {
        // Specular
        vec3 h = normalize(l + v);
        float NxH = saturate(dot(m.normal, h));
        float NxL = saturate(dot(m.normal, l));
        float LxH = saturate(dot(l, h));

        float D = brdf_distribution_ggx(NxH, m.roughness);
        vec3 F = brdf_schlick_fresnel(f0, LxH);
        float G = brdf_visibility_implicit(NxV, NxL);

        accum += brdf_cook_torrance(D, G, F, NxV, NxL) *
            approx_spot_light_specular_energy(m.roughness, fov);
    }
    {
        // Diffuse
        float att = 1.0 / max(0.01, length_squared(l_unscaled));
        float NxL = saturate(dot(m.normal, l));
        accum += att * NxL * get_material_diffuse(m);
    }

    accum *= shadow * light_scale * light_clip_falloff(light, m.position);
    accum *= get_light_color(light);

    return accum;

}


vec3 process_tubelight(Material m, LightData light, vec3 v, float shadow) {

    vec3 light_pos = get_light_position(light);

    float tube_radius = get_tube_radius(light);
    float tube_length = get_tube_length(light);
    vec3 tube_direction = get_tube_direction(light);

    #if !SPECIAL_MODE_ACTIVE(GROUND_TRUTH) && !HIGH_QUALITY_LIGHTING
        float NxV = saturate(dot(m.normal, v));
        vec3 l_unscaled = light_pos - m.position;

        vec3 accum = vec3(0);
        vec3 f0 = get_material_f0(m);
        {

            // Specular
            vec3 l_unscaled_spec = get_tube_area_light_vector(m.normal, light_pos, m.position, v, tube_radius, tube_length, tube_direction);

            vec3 l = normalize(l_unscaled_spec);
            vec3 h = normalize(l + v);

            float NxH = saturate(dot(m.normal, h));
            float NxL = saturate(dot(m.normal, l));
            float LxH = saturate(dot(l, h));

            float D = brdf_distribution_ggx(NxH, m.roughness);
            vec3 F = brdf_schlick_fresnel(f0, LxH);
            float G = brdf_visibility_neumann(NxV, NxL);

            accum += brdf_cook_torrance(D, G, F, NxV, NxL) *
                approx_tube_light_specular_energy(m.roughness, tube_length, tube_radius, dot(l_unscaled_spec, l_unscaled_spec));
        }

        {

            // Diffuse
            vec3 l_unscaled_diff = get_tube_area_light_diff_vector(m.position, light_pos, tube_radius, tube_length, tube_direction);
            vec3 l = normalize(l_unscaled_diff);
            float att = 1.0 / (dot(l_unscaled_diff, l_unscaled_diff) + 1);
            float NxL = saturate(dot(m.normal, l));

            // Luminous power -> luminance
            // XXX: Missing division by 4 * pi^2 here though. But matches mitsuba well. hm.
            float scale_factor = M_PI * (2.0 * M_PI * tube_radius * tube_length + 4.0 * M_PI * tube_radius * tube_radius);
            scale_factor *= approx_tube_light_diff_energy(tube_radius, tube_length);
            accum += att * NxL * get_material_diffuse(m) * scale_factor;
        }

        accum *= shadow;
        accum *= get_light_color(light);
        accum *= light_clip_falloff(light, m.position);
        return accum;

    #else

        // LTC for tube lights - good results, but slow
        vec3 l = normalize(light_pos - m.position);

        if (dot(m.normal, l) < 0.0)
            return vec3(0);

        vec3 h = normalize(l + v);

        vec3 right_vector = tube_direction;
        vec3 up_vector = cross(right_vector, l);

        up_vector *= tube_radius;
        right_vector *= (tube_length * 0.5) - tube_radius;

        const int num_points = 10;
        vec3 points[LTC_MAX_VERTICES];

        const float sqrt_05 = 0.7071067;

        // Approximate tube with 10 vertices:
        // 4 for the rectangle, and 6 for the circles at the sides
        points[0] = light_pos - right_vector - up_vector;
        points[1] = light_pos + right_vector - up_vector;

        points[2] = light_pos + right_vector + tube_radius * tube_direction * sqrt_05 - up_vector * sqrt_05;
        points[3] = light_pos + right_vector + tube_radius * tube_direction;
        points[4] = light_pos + right_vector + tube_radius * tube_direction * sqrt_05 + up_vector * sqrt_05;

        points[5] = light_pos + right_vector + up_vector;
        points[6] = light_pos - right_vector + up_vector;

        points[7] = light_pos - right_vector - tube_radius * tube_direction * sqrt_05 + up_vector * sqrt_05;
        points[8] = light_pos - right_vector - tube_radius * tube_direction;
        points[9] = light_pos - right_vector - tube_radius * tube_direction * sqrt_05 - up_vector * sqrt_05;

        vec2 coords = LTC_Coords(dot(m.normal, v), m.linear_roughness);
        mat3 minv = LTC_Matrix(LTCMatTex, coords);
        vec3 specular = LTC_Evaluate(m.normal, v, m.position, minv, points, num_points);
        vec3 diffuse = LTC_Evaluate(m.normal, v, m.position, mat3(1), points, num_points);

        vec3 f0 = get_material_f0(m);

        vec2 schlick = textureLod(LTCAmpTex, coords, 0).xy;
        specular *= f0 * schlick.x + (1.0 - f0) * schlick.y;
        diffuse *= get_material_diffuse(m);

        return (diffuse + specular) * get_light_color(light) * (light_clip_falloff(light, m.position) * shadow / TWO_PI);

    #endif

}

vec3 spherelight_specular_shading(vec3 normal, float roughness, vec3 f0, vec3 l_unscaled, vec3 v, float sphere_radius) {

    float NxV = saturate(dot(normal, v));
    vec3 l_unscaled_spec = get_spherical_area_light_vector(normal, l_unscaled, v, sphere_radius);

    vec3 l = normalize(l_unscaled_spec);
    vec3 h = normalize(l + v);

    float NxH = saturate(dot(normal, h));
    float NxL = saturate(dot(normal, l));
    float LxH = saturate(dot(l, h));

    float D = brdf_distribution_ggx(NxH, roughness);
    vec3 F = brdf_schlick_fresnel(f0, LxH);
    float G = brdf_visibility_neumann(NxV, NxL);

    return brdf_cook_torrance(D, G, F, NxV, NxL) *
        approx_sphere_light_specular_energy(roughness, sphere_radius, dot(l_unscaled_spec, l_unscaled_spec));
}

vec3 process_spherelight(Material m, LightData light, vec3 v, float shadow) {
    // #if SPECIAL_MODE_ACTIVE(GROUND_TRUTH)
    //     return process_spherelight_reference(m, light, v, shadow);
    // #endif

    vec3 light_pos = get_light_position(light);
    float sphere_radius = get_spherelight_sphere_radius(light);

    #if !SPECIAL_MODE_ACTIVE(GROUND_TRUTH) && !HIGH_QUALITY_LIGHTING
        vec3 l_unscaled = light_pos - m.position;

        vec3 specular = vec3(0);
        vec3 diffuse = vec3(0);
        vec3 f0 = get_material_f0(m);
        {

            // Specular
            specular = spherelight_specular_shading(m.normal, m.roughness, f0, l_unscaled, v, sphere_radius);

            BRANCH_CLEARCOAT(m) {
                vec3 specular_coat = spherelight_specular_shading(m.normal, CLEARCOAT_ROUGHNESS, vec3(CLEARCOAT_SPECULAR), l_unscaled, v, sphere_radius);
                specular = approx_merge_clearcoat_specular(specular, specular_coat);
            }

        }

        {
            // Diffuse
            vec3 l = normalize(l_unscaled);
            float att = 1.0 / (dot(l_unscaled, l_unscaled) + 1);
            float NxL = saturate(dot(m.normal, l));

            // Luminous power -> luminance
            // XXX: Missing division by 4 * pi^2 here though. But matches mitsuba well. hm.
            float scale_factor = sphere_radius * sphere_radius;
            diffuse = att * NxL * get_material_diffuse(m) * scale_factor;
        }

        vec3 accum = (diffuse + specular) * (shadow * light_clip_falloff(light, m.position));
        accum *= get_light_color(light);
        return accum;

    #else

        // LTC for sphere lights - good results, but slow
        vec3 l = normalize(light_pos - m.position);

        if (dot(m.normal, l) < 0.0)
            return vec3(0);

        vec3 h = normalize(l + v);

        vec3 up_vector, right_vector;
        find_arbitrary_tangent(l, right_vector, up_vector);

        up_vector *= sphere_radius;
        right_vector *= sphere_radius;

        const int num_points = LTC_MAX_VERTICES;
        vec3 points[LTC_MAX_VERTICES];

        for (int i = 0; i < num_points; ++i) {
            float phi = i / float(num_points) * TWO_PI;
            // Star
            // float radius = i % 2 == 0 ? 1.0 : 0.5;

            // Circle
            float radius = 1.0;
            points[i] = light_pos + sin(phi) * up_vector * radius + cos(phi) * right_vector * radius;
        }

        vec2 coords = LTC_Coords(dot(m.normal, v), m.linear_roughness);
        mat3 minv = LTC_Matrix(LTCMatTex, coords);
        vec3 specular = LTC_Evaluate(m.normal, v, m.position, minv, points, num_points);
        vec3 diffuse = LTC_Evaluate(m.normal, v, m.position, mat3(1), points, num_points);

        vec3 f0 = get_material_f0(m);

        vec2 schlick = textureLod(LTCAmpTex, coords, 0).xy;
        specular *= f0 * schlick.x + (1.0 - f0) * schlick.y;
        diffuse *= get_material_diffuse(m);

        return (diffuse + specular) * get_light_color(light) * (light_clip_falloff(light, m.position) * shadow / TWO_PI);

    #endif
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

    if (dot(m.normal, normalize(light_pos - m.position)) < 0.0)
        return vec3(0);

    vec2 coords = LTC_Coords(dot(m.normal, v), m.linear_roughness);
    mat3 minv = LTC_Matrix(LTCMatTex, coords);
    vec3 specular = LTC_EvaluateRect(m.normal, v, m.position, minv, points);
    vec3 diffuse = LTC_EvaluateRect(m.normal, v, m.position, mat3(1), points);

    vec3 f0 = get_material_f0(m);

    vec2 schlick = textureLod(LTCAmpTex, coords, 0).xy;
    specular *= f0 * schlick.x + (1.0 - f0) * schlick.y;
    diffuse *= get_material_diffuse(m);

    BRANCH_CLEARCOAT(m) {

        vec2 coords_coat = LTC_Coords(dot(m.normal, v), CLEARCOAT_ROUGHNESS);
        mat3 minv_coat = LTC_Matrix(LTCMatTex, coords_coat);
        vec3 specular_coat = LTC_EvaluateRect(m.normal, v, m.position, minv_coat, points);

        vec3 f0_coat = vec3(CLEARCOAT_SPECULAR);
        vec2 schlick_coat = textureLod(LTCAmpTex, coords_coat, 0).xy;
        specular_coat *= f0_coat * schlick_coat.x + (1.0 - f0_coat) * schlick_coat.y;

        specular = approx_merge_clearcoat_specular(specular, specular_coat);
    };

    return (diffuse + specular) * get_light_color(light) * (light_clip_falloff(light, m.position) * shadow / TWO_PI);
}
