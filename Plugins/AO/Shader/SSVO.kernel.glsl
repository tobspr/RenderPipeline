
/*

SSVO - Screen Space Volumetric Obscurance

This algorithm casts rays to a sphere arround the current point in view space,
and approximates the spheres volume by using line intetrals. The percentage
of the spheres volume is then used to compute AO.

*/

const int num_samples = GET_SETTING(AO, ssvo_sample_count);

float accum = 0.0;
float accum_count = 0;
vec2 sphere_radius = GET_SETTING(AO, ssvo_sphere_radius) * pixel_size;

float pixel_linz = getLinearZFromZ(pixel_depth);
float max_depth_diff = GET_SETTING(AO, ssvo_max_distance) / kernel_scale;


for (int i = 0; i < num_samples; ++i) {


    vec2 offset = poisson_disk_2D_32[i];
    offset += noise_vec.xy * 1.0;
    vec2 offc = offset * sphere_radius * 6.0 * kernel_scale;

    vec2 offcoord_a = texcoord + offc;
    vec2 offcoord_b = texcoord - offc;

    float sphere_height = ( 1 - dot(offset, offset) );

    float depth_a = get_depth_at(offcoord_a);
    float depth_b = get_depth_at(offcoord_b);

    float depth_linz_a = getLinearZFromZ(depth_a);
    float depth_linz_b = getLinearZFromZ(depth_b);

    float diff_a = (pixel_linz - depth_linz_a) / max_depth_diff;
    float diff_b = (pixel_linz - depth_linz_b) / max_depth_diff;

    float volume_a = (sphere_height - diff_a) / (2.0 * sphere_height);
    float volume_b = (sphere_height - diff_b) / (2.0 * sphere_height);

    bool valid_a = diff_a <= sphere_height && diff_a >= -sphere_height;
    bool valid_b = diff_b <= sphere_height && diff_b >= -sphere_height;


    if (valid_a || valid_b) {
        accum += valid_a ? volume_a : 1 - volume_b;  
        accum += valid_b ? volume_b : 1 - volume_a;  
    } else {
        accum += 1.0;
    }

}

// No bent normal supported yet, use pixel normal
vec3 bent_normal = pixel_world_normal;

accum /= num_samples;
accum = pow(accum, 3.8);
accum = saturate(accum);
result = vec4(bent_normal, accum);

