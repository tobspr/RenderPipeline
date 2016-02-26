/**
 *
 * RenderPipeline
 *
 * Copyright (c) 2014-2016 tobspr <tobias.springer1@gmail.com>
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 * THE SOFTWARE.
 *
 */

#pragma once

#pragma include "includes/transforms.inc.glsl"


// Controls the exponential factor, values < 1 produce a distribution closer to
// the camera, values > 1 produce a distribution which is further away from the camera.
#define SLICE_EXP_FACTOR 3.0


// Cell ray directions
const int num_raydirs = 5;


// Increase the frustum size by a small bit, because we trace at the corners,
// since using this way we could miss some small parts of the sphere. With this
// bias we should be fine, except for very small spheres, but those will be
// out of the culling range then anyays
const vec3 cull_bias = vec3(vec2(1 + 0.01), 1);
const vec3 aspect_mul = vec3(1, ASPECT_RATIO, 1);
CONST_ARRAY vec3 ray_dirs[num_raydirs] = vec3[](
    vec3( 0, 0, -1),
    vec3(  1.0,  1.0, -1) * cull_bias,
    vec3( -1.0,  1.0, -1) * cull_bias,
    vec3(  1.0, -1.0, -1) * cull_bias,
    vec3( -1.0, -1.0, -1) * cull_bias
);


int get_slice_from_distance(float dist) {
    float flt_dist = dist / LC_MAX_DISTANCE;
    return int(log(flt_dist * SLICE_EXP_FACTOR + 1.0) / log(1.0 + SLICE_EXP_FACTOR) * LC_TILE_SLICES);
    // return int(pow(dist / LC_MAX_DISTANCE, SLICE_POW_FACTOR) * LC_TILE_SLICES);
}

float get_distance_from_slice(int slice) {
    float flt_dist = slice / float(LC_TILE_SLICES) * log(1.0 + SLICE_EXP_FACTOR);
    float flt_exp = (exp(flt_dist) - 1.0) / SLICE_EXP_FACTOR;
    return flt_exp * LC_MAX_DISTANCE;
    // return pow(slice / float(LC_TILE_SLICES), 1.0 / SLICE_EXP_FACTOR) * LC_MAX_DISTANCE;
}

// Converts a coordinate and distance to the appropriate cell index
ivec3 get_lc_cell_index(ivec2 coord, float surface_distance) {
    ivec2 tile = coord / ivec2(LC_TILE_SIZE_X, LC_TILE_SIZE_Y);
    return ivec3(tile, get_slice_from_distance(surface_distance));
}

void unpack_cell_data(int packed_data, out int cell_x, out int cell_y, out int cell_slice) {
    cell_x = packed_data & 0x3FF;
    cell_y = (packed_data >> 10) & 0x3FF;
    cell_slice = (packed_data >> 20) & 0x3FF;
}

vec3 transform_raydir(vec3 dir, int cell_x, int cell_y, ivec2 precompute_size) {
    return normalize(fma((vec3(cell_x, cell_y, 0) + fma(dir, vec3(0.5), vec3(0.5)))
                    / vec3(precompute_size, 1), vec3(2.0), vec3(-1.0)) * aspect_mul);
}

// Interesects a sphere with a ray
// https://en.wikipedia.org/wiki/Line%E2%80%93sphere_intersection
bool ray_sphere_intersection(vec3 sphere_pos, float sphere_radius, vec3 ray_start, vec3 ray_dir, out float min_dist, out float max_dist) {
    // Get vector from ray to sphere
    vec3 o_minus_c = ray_start - sphere_pos;

    // Project that vector onto the ray
    float l_dot_o_minus_c = dot(ray_dir, o_minus_c);

    // Compute the distance
    float root = l_dot_o_minus_c * l_dot_o_minus_c - dot(o_minus_c, o_minus_c) + sphere_radius * sphere_radius;
    float sqr_root = sqrt(abs(root));

    min_dist = -l_dot_o_minus_c + sqr_root;
    max_dist = -l_dot_o_minus_c - sqr_root;

    return root > 0; // Can be >= 0 to include tangents as well.
}

// Intersect a sphere with a ray
bool viewspace_ray_sphere_intersection(vec3 sphere_pos, float sphere_radius, vec3 ray_dir, out float min_dist, out float max_dist) {
    return ray_sphere_intersection(sphere_pos, sphere_radius, vec3(0), ray_dir, min_dist, max_dist);
}

// Intersect a sphere with a ray, given a minimum and maximum ray distance
bool viewspace_ray_sphere_distance_intersection(vec3 sphere_pos, float sphere_radius, vec3 ray_dir, float tile_start, float tile_end) {
    float r_min, r_max;
    bool visible = viewspace_ray_sphere_intersection(sphere_pos, sphere_radius, ray_dir, r_min, r_max);
    return visible && r_max < tile_end && r_min > tile_start;
}

// Intersect a cone with a ray
bool viewspace_ray_cone_distance_intersection(vec3 cone_pos, vec3 cone_direction, float cone_radius, float cone_fov, vec3 ray_dir, float tile_start, float tile_end) {

    #if 1
        // Approximate the cone with a sphere
        // See: http://fs5.directupload.net/images/151219/xp2knkre.png
        float half_cone_radius = cone_radius * 0.5;
        vec3 sphere_center = cone_pos + cone_direction * half_cone_radius;
        float hypotenuse = cone_radius / cone_fov;

        // cone_fov is encoded as cos(cone_fov)
        // we can get the sin(cone_fov) using basic trigonometry:
        // From sin(x)^2 + cos(x)^2 = 1 we can derive:
        // sin(cone_fov) = sqrt(1 - cos(cone_fov) * cos(cone_fov))
        #if 0
            // Unoptimized version
            float opposite_side = sqrt(1.0 - cone_fov * cone_fov) * hypotenuse;
            float sphere_radius = sqrt(opposite_side * opposite_side + half_cone_radius * half_cone_radius);
        #else
            // Now to optimize this, we don't need the square root any longer:
            float opposite_side_sqr = (1.0 - cone_fov * cone_fov) * hypotenuse * hypotenuse;
            float sphere_radius = sqrt(opposite_side_sqr + half_cone_radius * half_cone_radius);
        #endif

        return viewspace_ray_sphere_distance_intersection(sphere_center, sphere_radius, ray_dir, tile_start, tile_end);
    #endif

    return true;
}
