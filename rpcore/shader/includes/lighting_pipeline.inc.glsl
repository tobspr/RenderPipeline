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
#pragma include "includes/pbr_lighting.inc.glsl"
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

// Sphere lights only store the index of their first shadow source,
// but they have 6 in total. This method finds the index offset of the
// shadow source, depending on the direction
int get_spherelight_shadow_source_offset(vec3 direction) {
    vec3 abs_dir = abs(direction);
    float max_comp = max3(abs_dir.x, abs_dir.y, abs_dir.z);
    if (abs_dir.x >= max_comp - 1e-5) return direction.x >= 0.0 ? 0 : 1;
    if (abs_dir.y >= max_comp - 1e-5) return direction.y >= 0.0 ? 2 : 3;
    return direction.z >= 0.0 ? 4 : 5;
}

// Filters a shadow map
float filter_shadowmap(Material m, SourceData source, vec3 l) {

    // TODO: Examine if this is faster
    // if (dot(m.normal, -l) < 0) return 0.0;

    mat4 mvp = get_source_mvp(source);
    vec4 uv = get_source_uv(source);

    float rotation = interleaved_gradient_noise(
        gl_FragCoord.xy + MainSceneData.frame_index % 32);
    mat2 rotation_mat = make_rotate_mat2(rotation);

    // TODO: make this configurable
    // XXX: Scale by resolution (higher resolution needs smaller bias)
    const float bias_mult = 0.1;
    const float slope_bias = 0.01 * bias_mult;
    const float normal_bias = 3 * bias_mult;
    const float const_bias = 0.01 * bias_mult;

    vec3 biased_pos = get_biased_position(m.position, slope_bias, normal_bias, m.normal, -l);

    vec3 projected = project(mvp, biased_pos);
    vec2 projected_coord = projected.xy * uv.zw + uv.xy;

    const int num_samples = 8;
    const float filter_size = 2.0 / SHADOW_ATLAS_SIZE;

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
    uint num_tube_noshadow      = min(LC_MAX_LIGHTS, texelFetch(PerCellLightsCounts, count_offs + 1 + LIGHT_CLS_TUBE_NOSHADOW).x);
    uint num_tube_shadow        = min(LC_MAX_LIGHTS, texelFetch(PerCellLightsCounts, count_offs + 1 + LIGHT_CLS_TUBE_SHADOW).x);

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
        SourceData source_data = read_source_data(ShadowSourceData, source_index * SHADOW_SOURCE_STRIDE);
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
        source_index += get_spherelight_shadow_source_offset(v2l);

        SourceData source_data = read_source_data(ShadowSourceData, source_index * SHADOW_SOURCE_STRIDE);
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
        SourceData source_data = read_source_data(ShadowSourceData, source_index * SHADOW_SOURCE_STRIDE);
        float shadow_factor = filter_shadowmap(m, source_data, v2l);
        shading_result += process_rectanglelight(m, light_data, v, shadow_factor);
    }

    // Tubelights without shadow
    for (int i = 0; i < num_tube_noshadow; ++i) {
        int light_offs = int(texelFetch(PerCellLights, curr_offs++).x);
        LightData light_data = read_light_data(AllLightsData, light_offs);
        shading_result += process_tubelight(m, light_data, v, 1.0);
    }

    // Tubelights with shadow
    for (int i = 0; i < num_tube_shadow; ++i) {
        int light_offs = int(texelFetch(PerCellLights, curr_offs++).x);
        LightData light_data = read_light_data(AllLightsData, light_offs);

        // Get shadow factor
        vec3 v2l = normalize(m.position - get_light_position(light_data));
        int source_index = get_shadow_source_index(light_data);
        SourceData source_data = read_source_data(ShadowSourceData, source_index * SHADOW_SOURCE_STRIDE);
        float shadow_factor = filter_shadowmap(m, source_data, v2l);
        shading_result += process_tubelight(m, light_data, v, shadow_factor);
    }


    // Fade out lights as they reach the culling distance
    float fade = saturate(linear_dist / LC_MAX_DISTANCE);
    fade = 1 - pow(fade, 10.0);


    // Debug mode, show tile bounds
    #if SPECIAL_MODE_ACTIVE(LIGHT_TILES)
        // Show tiles
        #if IS_SCREEN_SPACE

            if (num_total_lights > 0) {
        
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

                shading_result += vec3(render_number(tile_start + ivec2(3, 3), num_total_lights));
            
            }

        #endif
    #endif

    return shading_result * fade;
}
