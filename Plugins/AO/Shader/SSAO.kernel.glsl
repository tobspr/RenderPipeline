
/* 

CryEngine SSAO - Screen Space Ambient Occlusion

Samples the depth buffer in a hemisphere arround the current pixel to approximate
AO.

*/

const float sample_radius = GET_SETTING(AO, ssao_sample_radius);     
const int num_samples = GET_SETTING(AO, ssao_sample_count);
const float bias = GET_SETTING(AO, ssao_bias) * 0.5;
const float max_range = GET_SETTING(AO, ssao_max_distance);

float sample_offset = sample_radius * pixel_size.x;
float range_accum = 0.0;
float accum = 0.0;

vec3 bent_normal = vec3(0.0001);

for (int i = 0; i < num_samples; ++i) {

    vec3 offset = poisson_disk_3D_32[i];

    // Add noise
    offset += noise_vec * 0.3;
    offset /= 1.5;

    // Flip offset in case it faces away from the normal
    offset = faceforward(offset, offset, -pixel_view_normal);

    // Compute offset position in view space
    vec3 offset_pos = pixel_view_pos + offset * sample_offset * 20.0;

    // Project offset position to screen space
    vec3 projected = view_to_screen(offset_pos);

    // Fetch the expected depth
    float sample_depth = get_depth_at(projected.xy);

    // Linearize both depths
    float linz_a = get_linear_z_from_z(projected.z);
    float linz_b = get_linear_z_from_z(sample_depth);

    // Compare both depths by distance to find the AO factor
    float modifier = step(distance(linz_a, linz_b), max_range * 0.2);
    range_accum += modifier * 0.5 + 0.5;
    modifier *= step(linz_b + bias, linz_a);
    accum += modifier;

    // Update Bent Normal
    bent_normal += (1-modifier) * (offset);

}

bent_normal /= max(1.0, length(bent_normal));
bent_normal = view_normal_to_world(bent_normal);

// normalize samples
accum /= max(0.1, range_accum);

// Renormalize to match with the other techniques
accum *= 0.5;

result = vec4(bent_normal, 1 - saturate(accum));
