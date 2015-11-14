
/* 

CryEngine SSAO - Screen Space Ambient Occlusion

Samples the depth buffer in a hemisphere arround the current pixel to approximate
AO.

*/

const int num_samples = GET_SETTING(AO, ssao_sample_count);
const float bias = GET_SETTING(AO, ssao_bias) * 0.001;
const float max_range = GET_SETTING(AO, ssao_max_distance);

float sample_offset = sample_radius * pixel_size.x;
float range_accum = 0.0;
float accum = 0.0;

for (int i = 0; i < num_samples; ++i) {

    vec3 offset = poisson_disk_3D_32[i];

    // Add noise
    offset += noise_vec;
    offset /= 2.0;

    // Flip offset in case it faces away from the normal
    offset = faceforward(offset, offset, pixel_normal);

    // Compute offset position in view space
    vec3 offset_pos = pixel_view_pos + offset * sample_offset / kernel_scale * 20.0;

    // Project offset position to screen space
    vec3 projected = viewToScreen(offset_pos);

    // Fetch the expected depth
    float sample_depth = get_depth_at(projected.xy);

    // Linearize both depths
    float linz_a = getLinearZFromZ(projected.z);
    float linz_b = getLinearZFromZ(sample_depth);

    // Compare both depths by distance to find the AO factor
    float range_modifier = step(distance(linz_a, linz_b), max_range);
    range_accum += range_modifier * 0.5 + 0.5;
    accum += step(sample_depth + bias, projected.z) * range_modifier;

}

// normalize samples
accum /= max(0.1, range_accum);
result = vec4(1 - saturate(accum));
