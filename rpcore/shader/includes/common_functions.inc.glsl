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

// Not sure why GLSL does not define this
#define saturate(v) clamp(v, 0, 1)

#define M_PI 3.1415926535897932384626433
#define HALF_PI 1.5707963267948966192313216
#define TWO_PI 6.2831853071795864769252867
#define FOUR_PI 12.566370614359172953850573
#define ONE_BY_PI 0.3183098861837906715377675

#define AIR_IOR 1.000277

// Converts the cubemap direction, from Y-Up to Z-Up
vec3 cubemap_yup_to_zup(vec3 coord) {
    return normalize(coord.yxz * vec3(-1, 1, 1));
}

// Converts a texture coodinate in the range [0 .. 1] and face index to a direction vector
vec3 get_cubemap_coordinate(int face_index, vec2 coord) {
    vec3 baseDir = vec3(0);
    if (face_index == 0) baseDir = vec3(1.0, -coord.y, -coord.x);
    else if (face_index == 1) baseDir = vec3(-1.0, -coord.y, coord.x);
    else if (face_index == 2) baseDir = vec3(coord.x, 1.0, coord.y);
    else if (face_index == 3) baseDir = vec3(coord.x, -1.0, -coord.y);
    else if (face_index == 4) baseDir = vec3(coord.x, -coord.y, 1.0);
    else if (face_index == 5) baseDir = vec3(-coord.x, -coord.y, -1.0);
    return normalize(baseDir);
}

// Converts a coordinate like "gl_FragCoord" to a cubemap direction, with a given
// cubemap size. Assumes the render target has a size of (6 * cubemap_size, cubemap_size).
// clamped_coord will contain a coordinate from (0 .. cubemap_size), this can be
// used for further processing or writing the result.
// face will contain the selected cubemap face.
vec3 texcoord_to_cubemap(int cubemap_size, ivec2 coord, out ivec2 clamped_coord, out int face) {
    face = coord.x / cubemap_size;
    clamped_coord = coord % cubemap_size;
    vec2 local_coord = saturate((clamped_coord + 0.5) / float(cubemap_size)) * 2.0 - 1.0;
    return get_cubemap_coordinate(face, local_coord);
}

// Version of texcoord_to_cubemap without the out parameters
vec3 texcoord_to_cubemap(int cubemap_size, ivec2 coord) {
    ivec2 clamped_coord; int face;
    return texcoord_to_cubemap(cubemap_size, coord, clamped_coord, face);
}

// Returns a coordinate which can be used for bilateral upscaling, this returns a coordinate
// which should be used in full-res targets upscaling half-res targets
ivec2 get_bilateral_coord(ivec2 coord) {
    return (coord + 1) / 2 - 1;
}

// Checks if a 2D-coordinate is in the [0, 1] range
bool in_unit_rect(vec2 coord) {
    return coord.x >= 0.0 && coord.y >= 0.0 && coord.x <= 1.0 && coord.y <= 1.0;
}

// Checks if a 3D-coordinate is in the [0, 1] range
bool in_unit_box(vec3 coord) {
    return coord.x >= 0.0 && coord.y >= 0.0 && coord.z >= 0.0 &&
           coord.x <= 1.0 && coord.y <= 1.0 && coord.z <= 1.0;
}

// Finds a tangent and bitangent vector based on a given normal
void find_arbitrary_tangent(vec3 normal, out vec3 tangent, out vec3 bitangent) {
    vec3 v0 = abs(normal.z) < (0.99) ? vec3(0, 0, 1) : vec3(0, 1, 0);
    tangent = normalize(cross(v0, normal));
    bitangent = normalize(cross(tangent, normal));
}

// Returns the number of mipmaps of a cubemap
int get_mipmap_count(samplerCube cubemap) {
    int cubemap_size = textureSize(cubemap, 0).x;
    return int(1 + floor(log2(cubemap_size)));
}

// Converts a normalized spherical coordinate (r = 1) to cartesian coordinates
vec3 spherical_to_cartesian(float theta, float phi) {
    float sin_theta = sin(theta);
    return normalize(vec3(
        sin_theta * cos(phi),
        sin_theta * sin(phi),
        cos(theta)
    ));
}

// Converts a cartesian coordinate to spherical coordinates
void cartesian_to_spherical(vec3 v, out float theta, out float phi, out float radius) {
    radius = sqrt(dot(v, v));
    phi = acos(v.z / radius);
    theta = atan(v.y, v.x) + M_PI;
}

// Converts a normalized vector to spherical coordinates
void cartesian_to_spherical(vec3 v, out float theta, out float phi) {
    phi = acos(v.z);
    theta = atan(v.y, v.x) + M_PI;
}

// Converts a given sun azimuth and altitude to a direction vector
vec3 sun_azimuth_to_angle(float azimuth, float altitude) {
    float theta = (90 - altitude) / 180.0 * M_PI;
    float phi = azimuth / 180.0 * M_PI;
    return spherical_to_cartesian(theta, phi);
}

// Unpacks a normal from 0 .. 1 range to the -1 .. 1 range
vec3 unpack_texture_normal(vec3 n) {
    return fma(n, vec3(2.0), vec3(-1.0));
}

// Unpacks an integer from a float, packed by the GPUCommandQueue.
int gpu_cq_unpack_int_from_float(float v) {
    #if GPU_CMD_INT_AS_FLOAT
        return floatBitsToInt(v);
    #else
        return int(v);
    #endif
}

// Computes the diffuse antialiasing factor
// From: http://blog.selfshadow.com/sandbox/diffuse_aa.html
// float get_diffuse_aa(float w, float NxL) {
//     float x = sqrt(1.0 - w);
//     float x0 = 0.373837 * NxL;
//     float x1 = 0.66874 * x;
//     float n = x0 + x1;
//     return w * ((abs(x0) <= x1) ? n * n / x : saturate(NxL));
// }

// Blends a material
float blend_material(float material_factor, float detailmap, float add_factor, float pow_factor) {
    material_factor = max(0, material_factor);
    return saturate(
        mix(pow(max(0, detailmap + add_factor), pow_factor), 1.0, material_factor) *
        material_factor);
}

// Blends a specular IOR to make sure it never drops below 1.0
float blend_ior(float material_specular, float sampled_specular) {
    return 1.0 + max(0, material_specular - 1.0) * 2.0 * sampled_specular;
}

// We need to define them as macros instead of functions, since gl_FragCoord is
// not available in compute shaders

// Regular texcoord
#define get_texcoord() (gl_FragCoord.xy / SCREEN_SIZE)

// Texcoord for half-res targets sampling full-res targets
#define get_half_texcoord() vec2((ivec2(gl_FragCoord.xy) * 2 + 0.5) / SCREEN_SIZE)

// Texcoord for half-res targets sampling half-res targets
#define get_half_native_texcoord() (vec2(ivec2(gl_FragCoord.xy) + 0.5) / ivec2(SCREEN_SIZE / 2))

// Texcoord for quarter-res targets sampling full-res targets
#define get_quarter_texcoord() vec2((ivec2(gl_FragCoord.xy) * 4 + 0.5) / SCREEN_SIZE)

// Texcoord for quarter-res targets sampling quarter-res targets
#define get_quarter_native_texcoord() (vec2(ivec2(gl_FragCoord.xy) + 0.5) / ivec2(SCREEN_SIZE / 4))


// Converts from [0 .. SCREEN_SIZE] to [0 .. 1] including the +0.5 pixel offset to
// sample in the center of each pixel
vec2 int_coord_to_float(ivec2 coord) {
    return (coord + 0.5) / SCREEN_SIZE;
}

// Converts degree (0 .. 360) to radians (0 .. 2 PI)
float degree_to_radians(float degree) {
    return degree / 180.0 * M_PI;
}

// Simulates a near filter on a fullscreen texture
vec2 truncate_coordinate(vec2 tcoord, vec2 size) {
    return (ivec2(tcoord * size) + 0.5) / size;
}

vec2 truncate_coordinate(vec2 tcoord) {
    return truncate_coordinate(tcoord, SCREEN_SIZE);
}

// Returns the squared length of v
float length_squared(vec2 v) { return dot(v, v); }
float length_squared(vec3 v) { return dot(v, v); }
float length_squared(vec4 v) { return dot(v, v); }

// Squared distance between a and b
float distance_squared(vec3 a, vec3 b) { return length_squared(a - b); }
float distance_squared(vec4 a, vec4 b) { return length_squared(a - b); }
float distance_squared(vec2 a, vec2 b) { return length_squared(a - b); }

// Returns x * x
float square(float x) { return x * x; }
vec2 square(vec2 x) { return x * x; }
vec3 square(vec3 x) { return x * x; }
vec4 square(vec4 x) { return x * x; }

// Returns x * x * x * x
float pow4(float x) { float tmp = x * x; return tmp * tmp; }

// Minimum and maximum for multiple components
// XXX: There are hardware instructions (at least on AMD) for it:
// https://www.opengl.org/registry/specs/AMD/shader_trinary_minmax.txt
#define min3(a, b, c) min(a, min(b, c))
#define max3(a, b, c) max(a, max(b, c))
#define min4(a, b, c, d) min(a, min(b, min(c, d)))
#define max4(a, b, c, d) max(a, max(b, max(c, d)))
#define min5(a, b, c, d, e) min(a, min(b, min(c, min(d, e))))
#define max5(a, b, c, d, e) max(a, max(b, max(c, max(d, e))))

// Convenience function which ensures v dot n is > 0
vec3 face_forward(vec3 v, vec3 n) {
    return dot(v, n) < 0 ? -v : v;
}


// Computes a fade factor to fade out the given coordinates once
// they reach 0 / 1 on each component. Does not take aspect ratio into account
float compute_fade_factor(vec2 coords, float fade_range) {
    float fade = 1.0;
    fade *= saturate(min(coords.x, 1 - coords.x) / fade_range);
    fade *= saturate(min(coords.y, 1 - coords.y) / fade_range);
    return fade;
}

// Computes a fade factor to fade out the given coordinates once
// they reach 0 / 1 on each component. Also takes aspect ratio into account
float compute_screen_fade_factor(vec2 coords, float fade_range) {
    float fade = 1.0;
    fade *= saturate(min(coords.x, 1 - coords.x) / fade_range);
    fade *= saturate(min(coords.y, 1 - coords.y) / fade_range * ASPECT_RATIO);
    return fade;
}   

// Convenience functions for the scattering plugin - probably don't belong here
#define get_sun_vector() sun_azimuth_to_angle(TimeOfDay.scattering.sun_azimuth, TimeOfDay.scattering.sun_altitude)
#define get_sun_color() (TimeOfDay.scattering.sun_color * TimeOfDay.scattering.sun_intensity)
#define get_sun_color_scale(_v) saturate(square((_v.z) / 0.15))

#if REFERENCE_MODE
    #define SKYBOX_DIST 1000.0
#else
    #define SKYBOX_DIST 20000.0
#endif
