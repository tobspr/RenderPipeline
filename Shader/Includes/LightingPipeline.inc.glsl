#pragma once

#pragma include "Includes/Configuration.inc.glsl"
#pragma include "Includes/Structures/Material.struct.glsl"
#pragma include "Includes/LightCulling.inc.glsl"
#pragma include "Includes/Lights.inc.glsl"
#pragma include "Includes/LightData.inc.glsl"
#pragma include "Includes/Shadows.inc.glsl"
#pragma include "Includes/LightClassification.inc.glsl"

uniform isampler2DArray CellIndices;
uniform isamplerBuffer PerCellLights;
uniform samplerBuffer AllLightsData;
uniform samplerBuffer ShadowSourceData;

uniform sampler2D ShadowAtlas;
uniform sampler2DShadow ShadowAtlasPCF;

// Use ambient occlusion data, but only if we work in scren space, and only if
// the plugin is enabled
#if IS_SCREEN_SPACE && HAVE_PLUGIN(AO)
    uniform sampler2D AmbientOcclusion;
#endif

int get_pointlight_source_offs(vec3 direction) {
    vec3 abs_dir = abs(direction);
    float max_comp = max(abs_dir.x, max(abs_dir.y, abs_dir.z));
    if (abs_dir.x >= max_comp) return direction.x >= 0.0 ? 0 : 1;
    if (abs_dir.y >= max_comp) return direction.y >= 0.0 ? 2 : 3;
    return direction.z >= 0.0 ? 4 : 5;
}

// Processes a spot light
vec3 process_spotlight(Material m, LightData light_data, vec3 view_vector, vec4 directional_occlusion, float shadow_factor) {
    const vec3 transmittance = vec3(1); // <-- TODO

    // Get the lights data
    int ies_profile = get_ies_profile(light_data);
    vec3 position   = get_light_position(light_data);
    float radius    = get_spotlight_radius(light_data);
    float fov       = get_spotlight_fov(light_data);
    vec3 direction  = get_spotlight_direction(light_data);
    vec3 l          = normalize(position - m.position);

    // Compute the spot lights attenuation
    float attenuation = get_spotlight_attenuation(l, direction, fov, radius,
                                                  distance(m.position, position), ies_profile);

    // Compute the lights influence
    return apply_light(m, view_vector, l, get_light_color(light_data), attenuation,
                       shadow_factor, directional_occlusion, transmittance);
}

// Processes a point light
vec3 process_pointlight(Material m, LightData light_data, vec3 view_vector, vec4 directional_occlusion, float shadow_factor) {
    const vec3 transmittance = vec3(1); // <-- TODO

    // Get the lights data
    float radius    = get_pointlight_radius(light_data);
    vec3 light_pos  = get_light_position(light_data);
    int ies_profile = get_ies_profile(light_data);
    vec3 l          = normalize(light_pos - m.position);

    // Get the point light attenuation
    float attenuation = get_pointlight_attenuation(l, radius,
                                                   distance(m.position, light_pos), ies_profile);

    // Compute the lights influence
    return apply_light(m, view_vector, l, get_light_color(light_data),
                       attenuation, shadow_factor, directional_occlusion, transmittance);
}

// Filters a shadow map
float filter_shadowmap(Material m, SourceData source, vec3 l) {
    mat4 mvp = get_source_mvp(source);
    vec4 uv = get_source_uv(source);

    // TODO: make this configurable
    const float slope_bias = 0.001;
    const float normal_bias = 0.01;
    const float const_bias = 0.0002;
    vec3 biased_pos = get_biased_position(m.position, slope_bias, normal_bias, m.normal, l);

    // TODO: use filtering
    vec3 projected = project(mvp, biased_pos);
    vec2 projected_coord = projected.xy * uv.zw + uv.xy;
    return textureLod(ShadowAtlasPCF, vec3(projected_coord.xy, projected.z - const_bias), 0).x;
}



// Shades the material from the per cell light buffer
vec3 shade_material_from_tile_buffer(Material m, ivec3 tile) {

    #if DEBUG_MODE
        return vec3(0);
    #endif

    vec3 shading_result = vec3(0);

    // Find per tile lights
    int cell_index = texelFetch(CellIndices, tile, 0).x;
    int data_offs = cell_index * (MAX_LIGHTS_PER_CELL+LIGHT_CLS_COUNT);

    // Debug mode, show tile bounds
    #if 0
        // Show tiles
        #if IS_SCREEN_SPACE
            if (int(gl_FragCoord.x) % LC_TILE_SIZE_X == 0 || int(gl_FragCoord.y) % LC_TILE_SIZE_Y == 0) {
                shading_result += 0.01;
            }
            float light_factor = num_lights / float(MAX_LIGHTS_PER_CELL);
            shading_result += ( (tile.z + 1) % 2) * 0.01;
            // shading_result += light_factor;
        #endif
    #endif

    // Get directional occlusion
    vec4 directional_occlusion = vec4(0);
    #if IS_SCREEN_SPACE && HAVE_PLUGIN(AO)
        ivec2 coord = ivec2(gl_FragCoord.xy);
        directional_occlusion = normalize(texelFetch(AmbientOcclusion, coord, 0) * 2.0 - 1.0);
    #endif

    // Compute view vector
    vec3 v = normalize(MainSceneData.camera_pos - m.position);
    
    int curr_offs = data_offs + LIGHT_CLS_COUNT;

    // Get the light counts
    int num_spot_noshadow = texelFetch(PerCellLights, data_offs + LIGHT_CLS_SPOT_NOSHADOW).x;
    int num_spot_shadow = texelFetch(PerCellLights, data_offs + LIGHT_CLS_SPOT_SHADOW).x;
    int num_point_noshadow = texelFetch(PerCellLights, data_offs + LIGHT_CLS_POINT_NOSHADOW).x;
    int num_point_shadow = texelFetch(PerCellLights, data_offs + LIGHT_CLS_POINT_SHADOW).x;

    // Spotlights without shadow
    for (int i = 0; i < num_spot_noshadow; ++i) {
        int light_offs = texelFetch(PerCellLights, curr_offs++).x * 4;
        LightData light_data = read_light_data(AllLightsData, light_offs);
        shading_result += process_spotlight(m, light_data, v, directional_occlusion, 1.0);
    }

    // Spotlights with shadow
    for (int i = 0; i < num_spot_shadow; ++i) {
        int light_offs = texelFetch(PerCellLights, curr_offs++).x * 4;
        LightData light_data = read_light_data(AllLightsData, light_offs);

        // Get shadow factor
        vec3 v2l = normalize(m.position - get_light_position(light_data));
        int source_index = get_shadow_source_index(light_data);
        SourceData source_data = read_source_data(ShadowSourceData, source_index * 5);
        float shadow_factor = filter_shadowmap(m, source_data, v2l);
        shading_result += process_spotlight(m, light_data, v, directional_occlusion, shadow_factor);
    }

    // Pointlights without shadow
    for (int i = 0; i < num_point_noshadow; ++i) {
        int light_offs = texelFetch(PerCellLights, curr_offs++).x * 4;
        LightData light_data = read_light_data(AllLightsData, light_offs);
        shading_result += process_pointlight(m, light_data, v, directional_occlusion, 1.0);
    }

    // Pointlights with shadow
    for (int i = 0; i < num_point_shadow; ++i) {
        int light_offs = texelFetch(PerCellLights, curr_offs++).x * 4;
        LightData light_data = read_light_data(AllLightsData, light_offs);

        // Get shadow factor
        int source_index = get_shadow_source_index(light_data);
        vec3 v2l = normalize(m.position - get_light_position(light_data));
        source_index += get_pointlight_source_offs(v2l);

        SourceData source_data = read_source_data(ShadowSourceData, source_index * 5);
        float shadow_factor = filter_shadowmap(m, source_data, v2l);
        shading_result += process_pointlight(m, light_data, v, directional_occlusion, shadow_factor);
    }

    return shading_result;
}
