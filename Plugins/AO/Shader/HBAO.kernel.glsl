

const int num_angles = GET_SETTING(AO, hbao_ray_count);
const int num_ray_steps = GET_SETTING(AO, hbao_ray_steps);
const float tangent_bias = GET_SETTING(AO, hbao_tangent_bias);
const float max_sample_distance = GET_SETTING(AO, hbao_max_distance);

float accum = 0.0;

for (int i = 0; i < num_angles; ++i) {
    float angle = (i + 0.5 * noise_vec.x) / float(num_angles) * TWO_PI;

    vec2 sample_dir = vec2(cos(angle), sin(angle));

    // Find the tangent andle
    float tangent_angle = acos(dot(vec3(sample_dir, 0), pixel_normal)) - (0.5 * M_PI) + tangent_bias;

    // Assume the horizon angle is the same as the tangent angle at the beginning
    // of the ray
    float horizon_angle = tangent_angle;

    vec3 last_diff = vec3(0);

    // Raymarch in the sample direction
    for (int k = 0; k < num_ray_steps; ++k) {
        
        // Get new texture coordinate
        vec2 texc = texcoord + sample_dir * (k + 0.5) / num_ray_steps * pixel_size * sample_radius * 0.45;
        
        // Fetch view pos at that position and compare it
        vec3 view_pos = get_view_pos_at(texc);
        vec3 diff = view_pos - pixel_view_pos;

        if(length(diff) < max_sample_distance) {

            // Compute actual angle
            float sample_angle = atan(diff.z / length(diff.xy));

            // Correct horizon angle
            horizon_angle = max(horizon_angle, sample_angle);
            last_diff = diff;
        }
    }

    // Now that we know the average horizon angle, add it to the result
    // For that we simply take the angle-difference
    float occlusion = saturate(sin(horizon_angle) - sin(tangent_angle));
    // occlusion *= 1.0 / (1 + length(last_diff));
    accum += occlusion;    

}

// Normalize samples

accum /= num_angles;
// accum *= 5.0;
result = vec4(1 - accum);
