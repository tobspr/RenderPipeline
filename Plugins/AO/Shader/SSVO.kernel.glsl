
/*

SSVO - Screen Space Volumetric Obscurance

This algorithm casts rays to a sphere arround the current point in view space,
and approximates the spheres volume by using line intetrals. The percentage
of the spheres volume is then used to compute AO.

*/

const int num_samples = GET_SETTING(AO, ssvo_sample_count);

float accum = 0.0;
float accum_count = 0;
vec2 sphere_radius = GET_SETTING(AO, ssvo_sphere_radius) / kernel_scale * pixel_size;

float pixel_linz = getLinearZFromZ(pixel_depth);
float max_depth_diff = 10.0 / kernel_scale;


for (int i = 0; i < num_samples; ++i) {


    vec2 offset = poisson_disk_2D_32[i];
    offset += noise_vec.xy * 0.1;
    vec2 offcoord = texcoord + offset * sphere_radius * 5.0;

    float sphere_height = sqrt(  1 - dot(offset, offset) );


    float depth_a = get_depth_at(offcoord);
    float depth_linz = getLinearZFromZ(depth_a);

    float diff = (depth_linz - pixel_linz) / max_depth_diff;


    if (diff < sphere_height && diff > -sphere_height) {

        float percentage = (diff+sphere_height) / (2.0*sphere_height);
        accum += percentage;

        accum_count += 1.0;
    }

}
// accum /= num_samples;
accum /= max(1.0, accum_count);
accum = saturate(accum);
result = vec4(accum);

