
/*

DSSDO - Deferred Screen Space Directional Occlusion

Approximates average unocluded vector


*/


const int num_samples = 32;

float max_distance = 0.25;

vec4 accum = vec4(0);
float accum_count = 0.0;

for (int i = 0; i < num_samples; ++i) {

    vec3 offset = (poisson_disk_3D_64[i] + noise_vec.xyz * 0.4) * max_distance;
    offset = offset * sign(dot(offset, pixel_world_normal));

    vec3 offset_pos = pixel_world_pos + offset;

    vec3 offset_screen = worldToScreen(offset_pos);
    float actual_depth = get_depth_at(offset_screen.xy);
    vec3 actual_pos = calculateSurfacePos(actual_depth, offset_screen.xy);

    float expected_len = distance(cameraPosition, offset_pos);
    float actual_len = distance(cameraPosition, actual_pos);

    // if (actual_len < expected_len - 0.001 && actual_len > expected_len - 0.5 * max_distance) {
    if (actual_len > expected_len - 0.1) {

        float dist = distance(offset_pos, actual_pos);
        if (dist < max_distance) {
            accum += vec4(offset, 0.0);
            accum.w += 1.0 - dist / max_distance;
        }

        accum_count += 1.0;
    }
}

accum.w /= max(0.1, accum_count);
// accum.w /= num_samples;
accum.w = 1.0 - saturate( (accum.w - 0.2) * 1.4 );
accum.xyz /= max(1.0, length(accum.xyz));
result = vec4(accum);
// result = vec4(accum.xyz, 0);
// result = vec4(dot(accum.xyz, pixel_world_normal));
