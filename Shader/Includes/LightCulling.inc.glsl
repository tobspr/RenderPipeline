#pragma once

#pragma include "Includes/Configuration.inc.glsl"
#pragma include "Includes/PositionReconstruction.inc.glsl"
#pragma include "Includes/Structures/Frustum.struct.glsl"


#define LIGHT_CULLING_DIST LC_MAX_DISTANCE
#define SLICE_POW_FACTOR 1


int get_slice_from_distance(float dist) {
    return int( 
        pow(dist / LIGHT_CULLING_DIST, SLICE_POW_FACTOR) * LC_TILE_SLICES);
}

float get_distance_from_slice(int slice) {
    return pow(slice / float(LC_TILE_SLICES), 1.0 / SLICE_POW_FACTOR) * LIGHT_CULLING_DIST;
}

ivec3 getCellIndex(ivec2 coord, float surface_distance) {
    ivec2 tile = coord / ivec2(LC_TILE_SIZE_X, LC_TILE_SIZE_Y);
    return ivec3(tile, get_slice_from_distance(surface_distance));
}


bool sphere_frustum_intersection(Frustum frustum, vec4 pos, float radius) {
    bvec4 result;
    bvec2 result2;
    result.x = -radius <= dot(frustum.left, pos);
    result.y = -radius <= dot(frustum.right, pos);
    result.z = -radius <= dot(frustum.top, pos);
    result.w = -radius <= dot(frustum.bottom, pos);
    result2.x = -radius <= dot(frustum.nearPlane, pos);
    result2.y = -radius <= dot(frustum.farPlane, pos);
    return all(result) && all(result2);
}


bool ray_sphere_intersection(vec3 sphere_pos, float sphere_radius, vec3 ray_start, vec3 ray_dir, out float min_dist, out float max_dist) {
    // Assume ray_dir is normalized

    // https://en.wikipedia.org/wiki/Line%E2%80%93sphere_intersection
    // c = sphere_pos
    // r = sphere_radius
    // o = ray_start
    // l = ray_dir

    // Get vector from ray to sphere
    vec3 o_minus_c = ray_start - sphere_pos;

    // Project that vector onto the ray
    float l_dot_o_minus_c = dot(ray_dir, o_minus_c);

    // Compute the distance
    float root = l_dot_o_minus_c * l_dot_o_minus_c - dot(o_minus_c, o_minus_c) + sphere_radius * sphere_radius;
    float sqr_root = sqrt(abs(root));

    min_dist = -l_dot_o_minus_c + sqr_root;
    max_dist = -l_dot_o_minus_c - sqr_root; 


    return root > 0;
}


bool viewspace_ray_sphere_intersection(vec3 sphere_pos, float sphere_radius, vec3 ray_dir, out float min_dist, out float max_dist) {
    return ray_sphere_intersection(sphere_pos, sphere_radius, vec3(0), ray_dir, min_dist, max_dist);
}


bool viewspace_ray_sphere_distance_intersection(vec3 sphere_pos, float sphere_radius, vec3 ray_dir, float tile_start, float tile_end) {
    float r_min, r_max;
    bool visible = viewspace_ray_sphere_intersection(sphere_pos, sphere_radius, ray_dir, r_min, r_max);
    return visible && r_max < tile_end && r_min > tile_start;
}
