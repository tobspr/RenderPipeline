
/*

DSSDO - Deferred Screen Space Directional Occlusion

Approximates average unocluded vector


*/


const int num_samples = GET_SETTING(AO, dssdo_num_samples);
float max_distance = GET_SETTING(AO, dssdo_max_distance);

vec4 accum = vec4(0);
float accum_count = 0.0;

// @ TODO: Right now everything is in world space, because we need a world space
// normal. Maybe its better to do everything in view space, and transform the normal
// afterwards ...

for (int i = 0; i < num_samples; ++i) {

    // Get random offset in worldspace
    vec3 offset = (poisson_disk_3D_64[i] + noise_vec.xyz * 0.4) * max_distance;
    
    // Flip offset in case it faces away
    offset = faceforward(offset, offset, pixel_world_normal);

    vec3 offset_pos = pixel_world_pos + offset;

    // Get world pos at that random pos
    vec3 offset_screen = worldToScreen(offset_pos);
    float actual_depth = get_depth_at(offset_screen.xy);
    vec3 actual_pos = calculateSurfacePos(actual_depth, offset_screen.xy);

    // Compare the expected distance to the camera with the actual distance to
    // the camera
    float expected_len = distance(cameraPosition, offset_pos);
    float actual_len = distance(cameraPosition, actual_pos);

    // TODO: Remove ifs
    // Discard samples being ahead of the sphere
    if (actual_len > expected_len - 0.1) {

        // Discard samples being behind of the sphere
        float dist = distance(offset_pos, actual_pos);
        if (dist < max_distance) {
            accum += vec4(offset, 0.0);
            accum.w += 1.0 - dist / max_distance;
        }

        accum_count += 1.0;
    }
}

// Normalize ao value
accum.w /= max(0.1, accum_count);
accum.w = 1.0 - saturate( (accum.w - 0.2) * 1.4 );

// Normalize average occluded vector
accum.xyz /= max(1.0, length(accum.xyz));


result = vec4(accum);