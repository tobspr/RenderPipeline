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
#pragma include "includes/light_data.inc.glsl"

// Controls the exponential factor, values < 1 produce a distribution closer to
// the camera, values > 1 produce a distribution which is further away from the camera.
#define SLICE_EXP_FACTOR 3.0

// Set this to true to disable culling
#define DISABLE_CULLING 0

// Plane offsets
#define P_FRONT 0
#define P_BACK 1
#define P_LEFT 2
#define P_RIGHT 3
#define P_TOP 4
#define P_BOTTOM 5

// Sphere defined by origin and radius
struct Sphere {
    vec3 pos;
    float radius;
};

// Normalized plane with normal and distance to origin
struct Plane {
    vec3 N;
    float d;
};

// Frustum with 6 planes
struct Frustum {
    Plane planes[6];
    Sphere bsphere;
};

// Cone
struct Cone
{
    vec3 pos;
    float  height;
    vec3 direction;
    float  radius;
};

// Returns the slice index based on the distance
// TODO: Use tuned clustering sequence.
// Suggested from avalanche games is:
// [0.1, 5.0, 6.8, 9.2, 12.6, 17.1, 23.2, 31.5, 42.9, 58.3, 79.2, 108, 146, 199, 271, 368, 500]
int get_slice_from_distance(float dist) {
    float flt_dist = dist / LC_MAX_DISTANCE;
    return int(log(flt_dist * SLICE_EXP_FACTOR + 1.0) /
                log(1.0 + SLICE_EXP_FACTOR) * LC_TILE_SLICES);
}

// Returns the starting distance based on a slice index
float get_distance_from_slice(int slice) {
    float flt_dist = slice / float(LC_TILE_SLICES) * log(1.0 + SLICE_EXP_FACTOR);
    float flt_exp = (exp(flt_dist) - 1.0) / SLICE_EXP_FACTOR;
    return flt_exp * LC_MAX_DISTANCE;
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

// Returns the ray direction in view space for a given culling cell
vec3 transform_raydir(vec2 dir, int cell_x, int cell_y, ivec2 tile_size) {

    // We have to convert the cell position, because it might be that not all
    // tiles fit on screen (if the screen resolution is not a multiple of the tile size).
    // In this case, we are actually reconstructing a view space position outside of the
    // camera frustum, but due how the matrices work, this is fine.
    vec2 cell_pos = vec2(cell_x, cell_y) + dir * 0.5 + 0.5;
    cell_pos *= tile_size / SCREEN_SIZE;

    #if 0
        return reconstruct_vs_position(1, cell_pos);
    #else
        return mix(
            mix(MainSceneData.vs_frustum_directions[0],
                MainSceneData.vs_frustum_directions[1], cell_pos.x),
            mix(MainSceneData.vs_frustum_directions[2],
                MainSceneData.vs_frustum_directions[3], cell_pos.x),
            cell_pos.y
        ).xyz;
    #endif
}

// Computes a plane based on two points, the third point is assumed to be (0, 0, 0)
// since we do culling in viewspace
Plane compute_plane(vec3 p1, vec3 p2)
{
    Plane plane;
    plane.N = normalize(cross(p1, p2));
    plane.d = 0;
    return plane;
}

// Computes the six planes of the view frustum, or depending on the parameters, of the
// given culling cell
Frustum make_view_frustum(int cell_x, int cell_y, ivec2 tile_size, float min_dist, float max_dist) { 
    vec3 rd_tr = transform_raydir(vec2(1, 1), cell_x, cell_y, tile_size);
    vec3 rd_tl = transform_raydir(vec2(-1, 1), cell_x, cell_y, tile_size);
    vec3 rd_br = transform_raydir(vec2(1, -1), cell_x, cell_y, tile_size);
    vec3 rd_bl = transform_raydir(vec2(-1, -1), cell_x, cell_y, tile_size);

    Frustum view_frustum;

    view_frustum.planes[P_FRONT].N = vec3(0, 0, -1);
    view_frustum.planes[P_FRONT].d = min_dist;

    view_frustum.planes[P_BACK].N = vec3(0, 0, 1);
    view_frustum.planes[P_BACK].d = -max_dist;

    view_frustum.planes[P_LEFT] = compute_plane(rd_bl, rd_tl);
    view_frustum.planes[P_RIGHT] = compute_plane(rd_tr, rd_br);
    view_frustum.planes[P_TOP] = compute_plane(rd_tl, rd_tr);
    view_frustum.planes[P_BOTTOM] = compute_plane(rd_br, rd_bl);

    // Normalize ray directions, so that we can multiply with min_dist
    // to intersect the near plane, and multiply with max_dist to intersect the
    // far plane.
    rd_tr /= abs(rd_tr.z);
    rd_tl /= abs(rd_tl.z);
    rd_br /= abs(rd_br.z);
    rd_bl /= abs(rd_bl.z);

    // Compute average point of the culling voxel
    vec3 avg_planes = rd_tr + rd_tl + rd_br + rd_bl;
    vec3 avg_point = (min_dist * avg_planes + max_dist * avg_planes) / 8.0;

    // Find the radius of the bounding sphere arround this voxel for fast culling
    float avg_radius = sqrt(max(max(
        max(distance_squared(rd_tr * max_dist, avg_point),
            distance_squared(rd_tl * max_dist, avg_point)),
        max(distance_squared(rd_br * max_dist, avg_point),
            distance_squared(rd_bl * max_dist, avg_point))
    ), max(
        max(distance_squared(rd_tr * min_dist, avg_point),
            distance_squared(rd_tl * min_dist, avg_point)),
        max(distance_squared(rd_br * min_dist, avg_point),
            distance_squared(rd_bl * min_dist, avg_point))
    )));

    Sphere avg_sphere;
    avg_sphere.pos = avg_point;
    avg_sphere.radius = avg_radius;
    view_frustum.bsphere = avg_sphere;

    return view_frustum;
}


// http://www.3dgep.com/forward-plus/

// Check to see if a point is fully behind (inside the negative halfspace of) a plane.
bool point_inside_plane(vec3 p, Plane plane)
{
    return dot(plane.N, p) - plane.d < 0;
}

bool sphere_inside_plane(Sphere sphere, Plane plane)
{
    return dot(plane.N, sphere.pos) - plane.d < -sphere.radius;
}

bool sphere_inside_frustum(Sphere sphere, Frustum frustum)
{
    // Check frustum bounding sphere for fast check
    float d = distance_squared(sphere.pos, frustum.bsphere.pos);
    if (d > square(frustum.bsphere.radius + sphere.radius))
        return false;

    // Then check frustum planes
    for (int i = 0; i < 6; ++i) {
        if (sphere_inside_plane(sphere, frustum.planes[i]))
            return false;
    }
    return true;
}

// Check to see if a cone if fully behind (inside the negative halfspace of) a plane.
// Source: Real-time collision detection, Christer Ericson (2005)
bool cone_inside_plane(Cone cone, Plane plane)
{
    // Compute the farthest point on the end of the cone to the positive space of the plane.
    vec3 m = cross(cross(plane.N, cone.direction), cone.direction);
    vec3 Q = cone.pos + cone.direction * cone.height - m * cone.radius;
 
    // The cone is in the negative halfspace of the plane if both
    // the tip of the cone and the farthest point on the end of the cone to the 
    // positive halfspace of the plane are both inside the negative halfspace 
    // of the plane.
    return point_inside_plane(cone.pos, plane) && point_inside_plane(Q, plane );
}

bool cone_inside_frustum(Cone cone, Frustum frustum)
{
    for (int i = 0; i < 6; ++i)
    {
        if (cone_inside_plane(cone, frustum.planes[i]))
            return false;
    }
    return true;
}

bool cull_light(LightData light, Frustum view_frustum) {

    #if DISABLE_CULLING
        return true;
    #endif

    vec3 light_pos = (MainSceneData.view_mat_z_up * vec4(get_light_position(light), 1)).xyz;
    float radius = get_max_cull_distance(light);

    // Special case for spot lights, since we can cull them more efficient
    if (get_light_type(light) == LT_SPOT_LIGHT) {
        Cone cone;
        cone.pos = light_pos;
        cone.height = radius;
        
        // Need direction in view-space instead of world-space
        vec3 direction_ws = get_spotlight_direction(light);
        cone.direction = world_normal_to_view(direction_ws);

        // Compute radius from fov (fov is stored as cos(fov))
        float cos_cone_fov = get_spotlight_fov(light);
        float sin_cone_fov = sqrt(1 - cos_cone_fov * cos_cone_fov);

        float hypotenuse = cone.height / cos_cone_fov; 

        cone.radius = sin_cone_fov * hypotenuse; 
        return cone_inside_frustum(cone, view_frustum);
    }

    // Fallback for everything
    Sphere sphere;
    sphere.radius = radius;
    sphere.pos = light_pos; 
    return sphere_inside_frustum(sphere, view_frustum);

}
