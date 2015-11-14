
/*

SSVO - Screen Space Volumetric Obscurance

This algorithm casts rays to a sphere arround the current point in view space,
and approximates the spheres volume by using line intetrals. The percentage
of the spheres volume is then used to compute AO.

*/

const int num_samples = GET_SETTING(AO, ssvo_sample_count);

const float bias = 0.2;


float accum = 0.0;
float accum_count = 0;
float sphere_radius = GET_SETTING(AO, ssvo_sphere_radius);

for (int i = 0; i < num_samples; ++i) {

    // Compute offset in view space, in a sphere with the given radius
    // arround the current view space point
    vec3 offset = poisson_disk_3D_32[i];
    // offset += noise_vec * length(offset) * 0.5;
    // offset /= 2.0;
    // offset = normalize(offset);
    vec3 sample_pos = pixel_view_pos + offset * sphere_radius;

    // Project sample position to screen space
    vec3 proj = viewToScreen(sample_pos);

    // Project it back to view space, using the actual depth
    float proj_depth = get_depth_at(proj.xy);
    vec3 proj_surface = calculateViewPos(proj_depth, proj.xy);

    // Get ray properties. Our ray starts at (0, 0, 0) so we can simplify the 
    // equation by a lot
    vec3 ray_dir = normalize(sample_pos);
    vec3 sphere_center = pixel_view_pos;

    // Intersect ray with sphere
    // https://en.wikipedia.org/wiki/Line%E2%80%93sphere_intersection
    float ray_by_oc = dot(ray_dir, -sphere_center);
    float sqr = ray_by_oc * ray_by_oc - dot(sphere_center, sphere_center) + sphere_radius * sphere_radius;

    float dist_a = -(ray_by_oc) + sqrt(sqr);
    float dist_b = -(ray_by_oc) - sqrt(sqr);

    // Get intersection min and max point
    float dist_start = min(dist_a, dist_b);
    float dist_end = max(dist_a, dist_b);

    // Compute actual dist
    float real_dist = length(proj_surface);

    // Compute line integral
    float dist_factor = (real_dist - dist_start) / (dist_end - dist_start);

    // if (dist_factor > - bias && dist_factor < 2 + bias) {
        accum += saturate(dist_factor);
        // accum_count += 1.0;
        // accum_count += 0.75;
    // } 
    // accum_count += 0.25;
    accum_count += 1.0;
        // accum += 0.0;
        // accum_count += 0.1;
    // }

}

accum /= max(1.0, accum_count);

// Since on average, half of the sphere is occluded, multiply the factor by 2
// accum *= 2.0;
accum = saturate(accum);
result = vec4(accum);

