


const float sample_radius = GET_SETTING(AO, hbao_sample_radius);     
const int num_angles = GET_SETTING(AO, hbao_ray_count);
const int num_ray_steps = GET_SETTING(AO, hbao_ray_steps);
const float tangent_bias = GET_SETTING(AO, hbao_tangent_bias);
const float max_sample_distance = GET_SETTING(AO, hbao_max_distance) * 0.3;

float accum = 0.0;
vec3 bent_normal = vec3(pixel_view_normal * 3.0);

for (int i = 0; i < num_angles; ++i) {
    float angle = (i + 0.5 * noise_vec.x) / float(num_angles) * TWO_PI;

    vec2 sample_dir = vec2(cos(angle), sin(angle));

    // Find the tangent andle
    float tangent_angle = acos(dot(vec3(sample_dir, 0), pixel_view_normal)) - (0.5 * M_PI) + tangent_bias;

    // Assume the horizon angle is the same as the tangent angle at the beginning
    // of the ray
    float horizon_angle = tangent_angle;

    vec3 last_diff = vec3(0);

    // Raymarch in the sample direction
    for (int k = 0; k < num_ray_steps; ++k) {
        
        // Get new texture coordinate
        vec2 texc = texcoord + 
            sample_dir * (k + 0.5 + 0.3 * noise_vec.y) / 
                num_ray_steps * pixel_size * sample_radius * kernel_scale * 0.5;
        
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
    occlusion *= 1.0 / (1 + length(last_diff));
    accum += occlusion;

    // Update bent normal
    if (dot(abs(last_diff), vec3(1)) > 0.5) {
        bent_normal += (occlusion) * normalize(-last_diff);
    }
    // bent_normal += (last_diff);
    // bent_normal += normalize(last_diff);

}

// Normalize samples
accum /= num_angles;

// Normalize bent normal
bent_normal /= max(1.0, length(bent_normal));
bent_normal = view_normal_to_world(bent_normal);

result = vec4(bent_normal, 1 - 1.0*accum);
