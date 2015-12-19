#pragma once



#pragma include "Includes/Configuration.inc.glsl"
#pragma include "Includes/Structures/Material.struct.glsl"
#pragma include "Includes/LightCulling.inc.glsl"
#pragma include "Includes/Lights.inc.glsl"
#pragma include "Includes/LightData.inc.glsl"
#pragma include "Includes/BRDF.inc.glsl"

uniform isampler2DArray CellIndices;
uniform isamplerBuffer PerCellLights;
uniform samplerBuffer AllLightsData;

uniform vec3 cameraPosition;

// Use ambient occlusion data, but only if we work in scren space, and only if
// the plugin is enabled
#if IS_SCREEN_SPACE && HAVE_PLUGIN(AO)
    uniform sampler2D AmbientOcclusion;
#endif

// Shades the material from the per cell light buffer
vec3 shade_material_from_tile_buffer(Material m, ivec3 tile) {

    #if DEBUG_MODE
        return vec3(0);
    #endif

    vec3 shading_result = vec3(0);

    // Find per tile lights
    int cell_index = texelFetch(CellIndices, tile, 0).x;
    int data_offs = cell_index * (MAX_LIGHTS_PER_CELL+1);
    int num_lights = min(MAX_LIGHTS_PER_CELL, texelFetch(PerCellLights, data_offs).x);

    // Debug mode, show tile bounds
    #if 1
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
    vec3 v = normalize(cameraPosition - m.position);
        
    // Iterate over all lights
    for (int i = 0; i < num_lights; i++) {

        // Fetch light ID
        int light_offs = texelFetch(PerCellLights, data_offs + i + 1).x * 4;

        // Fetch per light packed data
        LightData light_data = read_light_data(AllLightsData, light_offs);
        int light_type = get_light_type(light_data);
        vec3 light_pos = get_light_position(light_data);
        int ies_profile = get_ies_profile(light_data);
        float attenuation = 0;
        vec3 l = vec3(0);

        // not implemented yet
        vec3 transmittance = vec3(1);

        // Special handling for different light types
        // TODO: Remove branches, by using seperate lists. Should be way faster
        switch(light_type) {

            case LT_POINT_LIGHT: {
                float radius = get_pointlight_radius(light_data);
                l = normalize(light_pos - m.position);
                attenuation = get_pointlight_attenuation(l, radius, distance(m.position, light_pos), ies_profile);
                break;
            } 
            case LT_SPOT_LIGHT: {
                
                float radius = get_spotlight_radius(light_data);
                float fov = get_spotlight_fov(light_data);
                vec3 direction = get_spotlight_direction(light_data);
                l = normalize(light_pos - m.position);
                attenuation = get_spotlight_attenuation(l, direction, fov, radius, distance(m.position, light_pos), ies_profile);
                break;
            }
        }

        shading_result += apply_light(m, v, l, get_light_color(light_data), attenuation, 1.0, directional_occlusion, transmittance);
    }
    
    return shading_result;
}