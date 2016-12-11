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
#pragma include "includes/light_culling.inc.glsl"
#pragma include "includes/lights.inc.glsl"
#pragma include "includes/light_data.inc.glsl"
#pragma include "includes/shadows.inc.glsl"
#pragma include "includes/noise.inc.glsl"
#pragma include "includes/light_classification.inc.glsl"
#pragma include "includes/poisson_disk.inc.glsl"
#pragma include "includes/matrix_ops.inc.glsl"
#pragma include "includes/debug_font.inc.glsl"

uniform isampler2DArray CellIndices;
uniform usamplerBuffer PerCellLights;
uniform usamplerBuffer PerCellLightsCounts;
uniform samplerBuffer AllLightsData;
uniform samplerBuffer ShadowSourceData;

uniform sampler2D ShadowAtlas;

#if SUPPORT_PCF
uniform sampler2DShadow ShadowAtlasPCF;
#endif

int get_pointlight_source_offs(vec3 direction) {
    vec3 abs_dir = abs(direction);
    float max_comp = max3(abs_dir.x, abs_dir.y, abs_dir.z);
    if (abs_dir.x >= max_comp - 1e-5) return direction.x >= 0.0 ? 0 : 1;
    if (abs_dir.y >= max_comp - 1e-5) return direction.y >= 0.0 ? 2 : 3;
    return direction.z >= 0.0 ? 4 : 5;
}

// Processes a spot light
vec3 process_spotlight(Material m, LightData light_data, vec3 view_vector, float shadow_factor) {
    const vec3 transmittance = vec3(1); // <-- TODO

    // Get the lights data
    int ies_profile = get_ies_profile(light_data);
    vec3 position = get_light_position(light_data);
    float radius = get_max_cull_distance(light_data);
    float fov = get_spotlight_fov(light_data);
    vec3 direction = get_spotlight_direction(light_data);
    vec3 l = position - m.position;
    vec3 l_norm = normalize(l);

    float attenuation = get_spotlight_attenuation(
        l_norm, direction, fov, radius, dot(l, l), ies_profile);

    // For spotlights, the specular term depends on the attenuation, for the reason
    // that the light emitter is not visible from all sides.
    // approximation
    vec2 energy = vec2(0.02, 0.01 * attenuation);

    // Compute the lights influence
    return apply_light(
        m, view_vector, l_norm, get_light_color(light_data), attenuation,
        shadow_factor, transmittance, energy, energy, l_norm);
}

// Processes a point light
vec3 process_spherelight(Material m, LightData light_data, vec3 view_vector, float shadow_factor) {
    const vec3 transmittance = vec3(1); // <-- TODO

    // Get the lights data
    float max_dist = get_max_cull_distance(light_data);
    float sphere_radius = get_spherelight_sphere_radius(light_data);
    vec3 position = get_light_position(light_data);
    int ies_profile = get_ies_profile(light_data);
    vec3 l = position - m.position;
    // float l_len_square = length_squared(l);

    // float dist_sq = l_len_square;
    vec3 l_diff = l;

    // Spherical area light
    // if (inner_radius > 0.02) {
    // l_diff = get_spherical_area_light_horizon(l, m.normal, inner_radius);
    // energy = get_spherical_area_light_energy(m.roughness, inner_radius, dist_sq);
    // dist_sq = max(0.01 * 0.01, square(sqrt(l_len_square) - inner_radius));
    // clearcoat_energy = get_spherical_area_light_energy(CLEARCOAT_ROUGHNESS, inner_radius, dist_sq);
    // }


    float dist = length(l); 
    // dist_sq *= dist_sq;

    vec2 energy = get_spherelight_energy(m.roughness, sphere_radius, dist);
    vec2 clearcoat_energy = energy;

    // l = get_spherical_area_light_vector(m.normal, l, view_vector, max(1.0, sphere_radius));
    l = get_spherical_area_light_vector(m.normal, l, view_vector, sphere_radius);
    
    // Get the point light attenuation
    // float attenuation = attenuation_curve(dist_sq, radius) * get_ies_factor(-l, ies_profile);
    float attenuation = attenuation_curve(dist * dist, max_dist); // * get_ies_factor(-l, ies_profile);

    // Compute the lights influence
    return apply_light(m, view_vector, normalize(l), get_light_color(light_data),
        attenuation, shadow_factor, transmittance, energy, clearcoat_energy, normalize(l_diff));
}


float rectangle_solid_angle(vec3 world_pos, vec3 p0, vec3 p1, vec3 p2, vec3 p3)
{
    vec3 v0 = p0 - world_pos;
    vec3 v1 = p1 - world_pos;
    vec3 v2 = p2 - world_pos;
    vec3 v3 = p3 - world_pos;
    vec3 n0 = normalize(cross(v0, v1));
    vec3 n1 = normalize(cross(v1, v2));
    vec3 n2 = normalize(cross(v2, v3));
    vec3 n3 = normalize(cross(v3, v0));
    float g0 = acos(dot(-n0, n1));
    float g1 = acos(dot(-n1, n2));
    float g2 = acos(dot(-n2, n3));
    float g3 = acos(dot(-n3, n0));
    return g0 + g1 + g2 + g3 - 2 * M_PI;
}

vec3 process_rectanglelight(Material m, LightData light_data, vec3 view_vector, float shadow_factor) {
    
    vec3 up_vector = get_rectangle_upvector(light_data);
    vec3 right_vector = get_rectangle_rightvector(light_data);
    vec3 light_pos = get_light_position(light_data);

    vec3 l_orig = m.position - light_pos;
    vec3 plane_normal = cross(up_vector, right_vector);

    if (dot(l_orig, plane_normal) > 0) {
        vec3 p0 = light_pos + right_vector + up_vector;
        vec3 p1 = light_pos + right_vector - up_vector;
        vec3 p2 = light_pos - right_vector - up_vector;
        vec3 p3 = light_pos - right_vector + up_vector;

        float solid_angle = rectangle_solid_angle(m.position, p0, p1, p2, p3);
        float illuminance = solid_angle * 0.2 * (
            saturate(dot(normalize(p0 - m.position), m.normal))  +
            saturate(dot(normalize(p1 - m.position), m.normal)) +
            saturate(dot(normalize(p2 - m.position), m.normal)) +
            saturate(dot(normalize(p3 - m.position), m.normal)) +
            saturate(dot(normalize(light_pos - m.position), m.normal)));

        vec3 ray_dir = normalize(reflect(-view_vector, m.normal));

        float d = dot(light_pos - m.position, plane_normal) / dot(ray_dir, plane_normal);
        vec3 plane_point = m.position + d * ray_dir;

        vec3 local_vec = plane_point - light_pos; // point on plane

        float u = dot(right_vector, local_vec) / length(right_vector);
        float v = dot(up_vector, local_vec) / length(up_vector);

        u = clamp(u, -1.0, 1.0);
        v = clamp(v, -1.0, 1.0);

        vec3 representative_point = light_pos + u * right_vector + v * up_vector;
        vec3 l = representative_point - m.position;

        float attenuation = illuminance;
        vec3 transmittance = vec3(1);
        vec2 energy = vec2(0.01, m.roughness * m.roughness * 0.03);
        vec2 clearcoat_energy = energy;
        vec3 l_diff = -l_orig;

        return apply_light(m, view_vector, normalize(l), get_light_color(light_data),
            attenuation, shadow_factor, transmittance, energy, clearcoat_energy, normalize(l_diff));
       
    }

    return vec3(0);



}



// Filters a shadow map
float filter_shadowmap(Material m, SourceData source, vec3 l) {

    // TODO: Examine if this is faster
    if (dot(m.normal, -l) < 0) return 0.0;

    mat4 mvp = get_source_mvp(source);
    vec4 uv = get_source_uv(source);

    float rotation = interleaved_gradient_noise(
        gl_FragCoord.xy + MainSceneData.frame_index % 32);
    mat2 rotation_mat = make_rotate_mat2(rotation);

    // TODO: make this configurable
    // XXX: Scale by resolution (higher resolution needs smaller bias)
    const float bias_mult = 0.01;
    const float slope_bias = 0.1 * bias_mult;
    const float normal_bias = 0.01 * bias_mult;
    const float const_bias = 0.0008 * bias_mult;


    vec3 biased_pos = get_biased_position(m.position, slope_bias, normal_bias, m.normal, -l);

    vec3 projected = project(mvp, biased_pos);
    vec2 projected_coord = projected.xy * uv.zw + uv.xy;

    const int num_samples = 8;
    const float filter_size = 3.0 / SHADOW_ATLAS_SIZE;

    float accum = 0.0;

    for (int i = 0; i < num_samples; ++i) {
        vec2 offs = projected_coord.xy + (rotation_mat * shadow_sample_offsets_8[i]) * filter_size;
        #if SUPPORT_PCF
            accum += textureLod(ShadowAtlasPCF, vec3(offs, projected.z - const_bias), 0).x;
        #else
            accum += textureLod(ShadowAtlas, vec2(offs), 0).x >
                projected.z - const_bias ? 1.0 : 0.0;
        #endif
    }

    return accum / num_samples;
}



// Shades the material from the per cell light buffer
vec3 shade_material_from_tile_buffer(Material m, ivec3 tile, float linear_dist) {

    #if DEBUG_MODE && !SPECIAL_MODE_ACTIVE(LIGHT_TILES)
        return vec3(0);
    #endif

    // Skip emissive materials
    if (m.shading_model == SHADING_MODEL_EMISSIVE)
        return vec3(0);

    vec3 shading_result = vec3(0);

    // Find per tile lights
    int cell_index = texelFetch(CellIndices, tile, 0).x;
    int count_offs = cell_index * (1 + LIGHT_CLS_COUNT); // 1 for total count, rest for light classes
    uint num_total_lights = texelFetch(PerCellLightsCounts, count_offs).x;

    // Early out when no lights are there
    #if !SPECIAL_MODE_ACTIVE(LIGHT_TILES)
        if (num_total_lights == 0) {
            return vec3(0);
        }
    #endif

    // Get the per-class light counts
    // To be safe, we use a min() to avoid huge loops in case some texture is not cleared or so.
    uint num_spot_noshadow      = min(LC_MAX_LIGHTS, texelFetch(PerCellLightsCounts, count_offs + 1 + LIGHT_CLS_SPOT_NOSHADOW).x);
    uint num_spot_shadow        = min(LC_MAX_LIGHTS, texelFetch(PerCellLightsCounts, count_offs + 1 + LIGHT_CLS_SPOT_SHADOW).x);
    uint num_sphere_noshadow    = min(LC_MAX_LIGHTS, texelFetch(PerCellLightsCounts, count_offs + 1 + LIGHT_CLS_SPHERE_NOSHADOW).x);
    uint num_sphere_shadow      = min(LC_MAX_LIGHTS, texelFetch(PerCellLightsCounts, count_offs + 1 + LIGHT_CLS_SPHERE_SHADOW).x);
    uint num_rectangle_noshadow = min(LC_MAX_LIGHTS, texelFetch(PerCellLightsCounts, count_offs + 1 + LIGHT_CLS_RECTANGLE_NOSHADOW).x);
    uint num_rectangle_shadow   = min(LC_MAX_LIGHTS, texelFetch(PerCellLightsCounts, count_offs + 1 + LIGHT_CLS_RECTANGLE_SHADOW).x);

    // Compute the index into the culled lights list
    int data_offs = cell_index * LC_MAX_LIGHTS_PER_CELL;
    int curr_offs = data_offs;

    #if IS_SCREEN_SPACE
        ivec2 tile_start = ivec2(tile.x, tile.y) * ivec2(LC_TILE_SIZE_X, LC_TILE_SIZE_Y);
    #endif

    vec3 v = normalize(MainSceneData.camera_pos - m.position);

    // Spotlights without shadow
    for (int i = 0; i < num_spot_noshadow; ++i) {
        int light_offs = int(texelFetch(PerCellLights, curr_offs++).x);
        LightData light_data = read_light_data(AllLightsData, light_offs);
        shading_result += process_spotlight(m, light_data, v, 1.0);
    }

    // Spotlights with shadow
    for (int i = 0; i < num_spot_shadow; ++i) {
        int light_offs = int(texelFetch(PerCellLights, curr_offs++).x);
        LightData light_data = read_light_data(AllLightsData, light_offs);

        // Get shadow factor
        vec3 v2l = normalize(m.position - get_light_position(light_data));
        int source_index = get_shadow_source_index(light_data);
        SourceData source_data = read_source_data(ShadowSourceData, source_index * 5);
        float shadow_factor = filter_shadowmap(m, source_data, v2l);
        shading_result += process_spotlight(m, light_data, v, shadow_factor);
    }
    
    // Spherelights without shadow
    for (int i = 0; i < num_sphere_noshadow; ++i) {
        int light_offs = int(texelFetch(PerCellLights, curr_offs++).x);
        LightData light_data = read_light_data(AllLightsData, light_offs);
        shading_result += process_spherelight(m, light_data, v, 1.0);
    }

    // Spherelights with shadow
    for (int i = 0; i < num_sphere_shadow; ++i) {
        int light_offs = int(texelFetch(PerCellLights, curr_offs++).x);
        LightData light_data = read_light_data(AllLightsData, light_offs);

        // Get shadow factor
        int source_index = get_shadow_source_index(light_data);
        vec3 v2l = normalize(m.position - get_light_position(light_data));
        source_index += get_pointlight_source_offs(v2l);

        SourceData source_data = read_source_data(ShadowSourceData, source_index * 5);
        float shadow_factor = filter_shadowmap(m, source_data, v2l);
        shading_result += process_spherelight(m, light_data, v, shadow_factor);
    }

    
    // Rectanglelights without shadow
    for (int i = 0; i < num_rectangle_noshadow; ++i) {
        int light_offs = int(texelFetch(PerCellLights, curr_offs++).x);
        LightData light_data = read_light_data(AllLightsData, light_offs);
        shading_result += process_rectanglelight(m, light_data, v, 1.0);
    }

    // Rectanglelights with shadow
    for (int i = 0; i < num_rectangle_shadow; ++i) {
        int light_offs = int(texelFetch(PerCellLights, curr_offs++).x);
        LightData light_data = read_light_data(AllLightsData, light_offs);

        // Get shadow factor
        vec3 v2l = normalize(m.position - get_light_position(light_data));
        int source_index = get_shadow_source_index(light_data);
        SourceData source_data = read_source_data(ShadowSourceData, source_index * 5);
        float shadow_factor = filter_shadowmap(m, source_data, v2l);
        shading_result += process_rectanglelight(m, light_data, v, shadow_factor);
    }


    // Fade out lights as they reach the culling distance
    float fade = saturate(linear_dist / LC_MAX_DISTANCE);
    fade = 1 - pow(fade, 10.0);


    // Debug mode, show tile bounds
    #if SPECIAL_MODE_ACTIVE(LIGHT_TILES)
        // Show tiles
        #if IS_SCREEN_SPACE

            // if (num_total_lights > 0) {
        
                float light_factor = num_total_lights / float(LC_MAX_LIGHTS_PER_CELL);
                shading_result = saturate(shading_result) * 0.2;
        
        
                if (int(gl_FragCoord.x) % LC_TILE_SIZE_X == 0 ||
                    int(gl_FragCoord.y) % LC_TILE_SIZE_Y == 0) {
                    shading_result += 0.1;
                }
                
                // shading_result += light_factor;
                vec3 bg_color = vec3(0, 1, 0);
                
                if (num_total_lights > 5) {
                    bg_color = vec3(1, 1, 0);
                }

                if (num_total_lights > 10) {
                    bg_color = vec3(1, 0, 0);
                }

                if (num_total_lights == LC_MAX_LIGHTS_PER_CELL) {
                    bg_color = vec3(10, 0, 0);
                }

                shading_result += bg_color * 0.2;

                // shading_result += ((tile.z + 1) % 2) * 0.05;

                shading_result += vec3(render_number(tile_start + ivec2(3, 3), num_total_lights));
            
            // }

        #endif
    #endif

    return shading_result * fade;
}
