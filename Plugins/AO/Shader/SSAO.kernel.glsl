
// CryEngine SSAO
// Samples the depth buffer in a sphere arround the current pixel

const int num_samples = GET_SETTING(AO, ssao_sample_count);
const float bias = GET_SETTING(AO, ssao_bias) * 0.001;
const float max_range = GET_SETTING(AO, ssao_max_distance);

float sample_offset = sample_radius * pixel_size.x;
float range_accum = 0.0;
float accum = 0.0;
for (int i = 0; i < num_samples; ++i) {

    vec3 offset = poisson_disk_3D_32[i];

    offset += noise_vec;
    // offset = normalize(offset);

    // Flip offset in case it faces away from the normal
    offset = offset * sign(dot(offset, pixel_normal));

    vec3 offset_pos = pixel_view_pos + offset * sample_offset / kernel_scale * 20.0;

    vec4 projected = currentProjMat * vec4(offset_pos, 1);
    projected.xyz /= projected.w;
    projected.xy = fma(projected.xy, vec2(0.5), vec2(0.5));
    float sample_depth = get_depth_at(projected.xy);


    float linz_a = getLinearZFromZ(projected.z);
    float linz_b = getLinearZFromZ(sample_depth);

    float range_modifier = step(distance(linz_a, linz_b), max_range);

    range_accum += range_modifier * 0.5 + 0.5;
    accum += step(sample_depth + bias, projected.z) * range_modifier;

}

accum /= max(0.1, range_accum);


result = vec4(1 - accum);