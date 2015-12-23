#version 430

#pragma include "Includes/Configuration.inc.glsl"
#pragma include "Includes/PositionReconstruction.inc.glsl"
#pragma include "Includes/LightCulling.inc.glsl"
#pragma include "Includes/LightData.inc.glsl"

uniform isamplerBuffer CellListBuffer;
uniform writeonly iimageBuffer PerCellLightsBuffer;

uniform samplerBuffer AllLightsData;
uniform int maxLightIndex;

void main() {

    ivec2 coord = ivec2(gl_FragCoord.xy);

    // Find the index of the cell we are about to process
    int idx = coord.x + coord.y * LC_CULLING_SLICE_WIDTH + 1;
    int num_total_cells = texelFetch(CellListBuffer, 0).x;
    ivec2 precompute_size = ivec2(LC_TILE_AMOUNT_X, LC_TILE_AMOUNT_Y);

    // If we found no remaining cell, we are done, so just return and hope for
    // good coherency.
    if (idx > num_total_cells) {
        // Could use return here. Not sure whats faster. Have to test it.
        discard;
    }

    // Fetch the cell data, this contains the cells position
    int packed_cell_data = texelFetch(CellListBuffer, idx).x;
    int cell_x = packed_cell_data & 0x3FF;
    int cell_y = (packed_cell_data >> 10) & 0x3FF;
    int cell_slice = (packed_cell_data >> 20) & 0x3FF;

    // Amount to increment the minimum and maximum distance of the slice. This
    // avoids false negatives in culling.
    float distance_bias = 0.01;

    // Find the tiles minimum and maximum distance
    float min_distance = get_distance_from_slice(cell_slice) - distance_bias;
    float max_distance = get_distance_from_slice(cell_slice + 1) + distance_bias;

    // Get the offset in the per-cell light list
    int storage_offs = (MAX_LIGHTS_PER_CELL+1) * idx;
    int num_rendered_lights = 0;

    // Compute the aspect ratio, this is required for proper culling.
    float aspect = float(WINDOW_HEIGHT) / WINDOW_WIDTH;
    vec3 aspect_mul = vec3(1, aspect, 1);

    // Increase the frustum size by a small bit, because we trace at the corners,
    // since using this way we could miss some small parts of the sphere. With this
    // bias we should be fine, except for very small spheres, but those will be
    // out of the culling range then anyays
    float cull_bias = 1 + 0.01;

    // Compute sample directions
    const int num_raydirs = 5;
    vec3 ray_dirs[num_raydirs] = vec3[](
        // Center
        vec3( 0, 0, -1),
        
        // Corners
        vec3(  1.0,  1.0, -1) * cull_bias,
        vec3( -1.0,  1.0, -1) * cull_bias,
        vec3(  1.0, -1.0, -1) * cull_bias,
        vec3( -1.0, -1.0, -1) * cull_bias
    );

    // Generate ray directions
    for (int i = 0; i < num_raydirs; ++i) {
        ray_dirs[i] = normalize( 
            fma( (vec3(cell_x, cell_y, 0) + fma(ray_dirs[i], vec3(0.5), vec3(0.5)) ) 
                    / vec3(precompute_size, 1), vec3(2.0), vec3(-1.0)) * aspect_mul);
    }

    // Cull all lights
    for (int i = 0; i < maxLightIndex + 1 && num_rendered_lights < MAX_LIGHTS_PER_CELL; i++) {

        // Fetch data of current light
        LightData light_data = read_light_data(AllLightsData, i * 4);
        int light_type = get_light_type(light_data);

        // Skip Null-Lights
        if (light_type < 1) continue;

        // Get Light position and project it to view space
        vec3 light_pos = get_light_position(light_data);
        vec4 light_pos_view = MainSceneData.view_mat_z_up * vec4(light_pos, 1);

        bool visible = false;

        // Point Lights
        switch(light_type) {

            case LT_POINT_LIGHT: {
                float radius = get_pointlight_radius(light_data);
                for (int k = 0; k < num_raydirs; ++k) {
                    visible = visible || viewspace_ray_sphere_distance_intersection(light_pos_view.xyz, radius, ray_dirs[k], min_distance, max_distance);
                }
                break;
            } 

            case LT_SPOT_LIGHT: {
                float radius = get_spotlight_radius(light_data);
                vec3 direction = get_spotlight_direction(light_data);
                vec3 direction_view = world_normal_to_view(direction);
                float fov = get_spotlight_fov(light_data);
                for (int k = 0; k < num_raydirs; ++k) {
                    visible = visible || viewspace_ray_cone_distance_intersection(light_pos_view.xyz, direction_view, radius, fov, ray_dirs[k], min_distance, max_distance);
                }
                break;
            }
        }

        // Write the light to the light buffer
        // TODO: Might have a seperate list for different light types, gives better performance
        if (visible) {
            num_rendered_lights ++;
            imageStore(PerCellLightsBuffer, storage_offs + num_rendered_lights, ivec4(i));
        }
    }

    imageStore(PerCellLightsBuffer, storage_offs, ivec4(num_rendered_lights));
}
