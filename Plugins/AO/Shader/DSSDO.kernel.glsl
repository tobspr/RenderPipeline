
/*

DSSDO - Deferred Screen Space Directional Occlusion

Approximates average unocluded vector

Based on:
https://github.com/kayru/dssdo/blob/master/dssdo.hlsl

*/


const int num_samples = 32;

const float max_distance = 0.4;

vec4 accum = vec4(0);

for (int i = 0; i < num_samples; ++i) {

    vec3 offset = (poisson_disk_3D_32[i] + noise_vec.xyz * 0.3) * max_distance;
    offset = offset * sign(dot(offset, pixel_world_normal));

    vec3 offset_pos = pixel_world_pos + offset * max_distance;

    vec3 offset_screen = worldToScreen(offset_pos);
    float actual_depth = get_depth_at(offset_screen.xy);
    vec3 actual_pos = calculateSurfacePos(actual_depth, offset_screen.xy);

    float expected_len = distance(cameraPosition, offset_pos);
    float actual_len = distance(cameraPosition, actual_pos);

    if (actual_len < expected_len - 0.001 && actual_len > expected_len - 0.5 * max_distance) {
        accum += vec4(offset, 1.0);
    }

}

accum.w /= num_samples;
accum.xyz /= max(1.0, length(accum.xyz));
result = vec4(accum);
