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

// GBuffer include Version 2

#pragma once

/*

GBuffer Layout:
TODO: We could move shading model and param 0 to data1, and make it 8 bit. Need to
      support different aux attachments then though.

Depth[D32F]:     [Depth                                                   ]
Data0[RGBA16F]:  [Basecolor R] [Basecolor G] [Basecolor B]   [Roughness   ]
Data1[RGBA16F]:  [Normal X]    [Normal Y]    [Metallic]      [Specular IOR]
Data2[RGBA16F]:  [Velocity X]  [Velocity Y]  [Shading Model] [SM Param 0  ]


SM Param 0 is an arbitrary parameter that depends on the shading model, for
transparent objects it determines the alpha for example.

*/
uniform struct {
    sampler2D Depth;
    sampler2D Data0;
    sampler2D Data1;
    sampler2D Data2;
} GBuffer;


#pragma include "includes/normal_packing.inc.glsl"
#pragma include "includes/material.inc.glsl"
#pragma include "includes/transforms.inc.glsl"


//
// Skybox
//

bool is_skybox(vec3 pos, vec3 camera_pos) {
    return distance(pos, camera_pos) > SKYBOX_DIST;
}

bool is_skybox(Material m, vec3 camera_pos) {
    return is_skybox(m.position, camera_pos);
}

bool is_skybox(Material m) {
    return is_skybox(m, MainSceneData.camera_pos);
}

bool is_skybox(vec3 pos) {
    return is_skybox(pos, MainSceneData.camera_pos);
}

bool needs_shading(Material m) {
    return !is_skybox(m) && m.shading_model != SHADING_MODEL_EMISSIVE;
}


//
// GBuffer methods
//

// Depth
float gbuffer_get_depth(vec2 coord) {
    return textureLod(GBuffer.Depth, coord, 0).x;
}

float gbuffer_get_depth(ivec2 coord) {
    return texelFetch(GBuffer.Depth, coord, 0).x;
}

// Linear Depth
float gbuffer_get_linear_depth_32bit(vec2 coord) {
    return get_linear_z_from_z(gbuffer_get_depth(coord));
}

float gbuffer_get_linear_depth_32bit(ivec2 coord) {
    return get_linear_z_from_z(gbuffer_get_depth(coord));
}

// Normal
vec3 gbuffer_get_normal(vec2 coord) {
    vec2 packed_normal = textureLod(GBuffer.Data1, coord, 0).xy;
    return unpack_normal_octahedron(packed_normal);
}

vec3 gbuffer_get_normal(ivec2 coord) {
    vec2 packed_normal = texelFetch(GBuffer.Data1, coord, 0).xy;
    return unpack_normal_octahedron(packed_normal);
}

// Shading model
int gbuffer_get_shading_model(vec2 coord) {
    return int(textureLod(GBuffer.Data2, coord, 0).z);
}

int gbuffer_get_shading_model(ivec2 coord) {
    return int(texelFetch(GBuffer.Data2, coord, 0).z);
}

// Per-Object Velocity
vec2 gbuffer_get_object_velocity(vec2 coord) {
    return textureLod(GBuffer.Data2, coord, 0).xy;
}

vec2 gbuffer_get_object_velocity(ivec2 coord) {
    return texelFetch(GBuffer.Data2, coord, 0).xy;
}

// Whole material
Material gbuffer_get_material(vec2 coord) {
    float depth = textureLod(GBuffer.Depth, coord, 0).x;
    vec4  data0 = textureLod(GBuffer.Data0, coord, 0);
    vec4  data1 = textureLod(GBuffer.Data1, coord, 0);
    vec4  data2 = textureLod(GBuffer.Data2, coord, 0);

    Material m;
    m.position = reconstruct_ws_position(depth, coord);
    m.basecolor = data0.xyz;
    m.linear_roughness = clamp(data0.w, MINIMUM_ROUGHNESS, 1.0);
    m.roughness = m.linear_roughness * m.linear_roughness;
    m.normal = unpack_normal_octahedron(data1.xy);
    m.metallic = saturate(data1.z * 1.001 - 0.0005); // Prevents precision issues
    m.specular_ior = data1.w;
    m.specular = ior_to_specular(data1.w);
    m.shading_model = int(data2.z);
    m.shading_model_param0 = data2.w;

    // Velocity, not stored in the Material struct but stored in the G-Buffer
    // vec2 velocity = data2.xy;
    return m;

}

Material gbuffer_get_material(ivec2 coord) {
    return gbuffer_get_material(int_coord_to_float(coord));
}

Material gbuffer_get_material() {
    return gbuffer_get_material(get_texcoord());
}


//
// GBuffer helpers
//

// World-Space Position
vec3 gbuffer_reconstruct_ws_position(vec2 coord) {
    float depth = gbuffer_get_depth(coord);
    return reconstruct_ws_position(depth, coord);
}

vec3 gbuffer_reconstruct_ws_position(ivec2 coord) {
    return gbuffer_reconstruct_ws_position(int_coord_to_float(coord));
}

// View-Space Position
vec3 gbuffer_reconstruct_vs_position(vec2 coord) {
    float depth = gbuffer_get_depth(coord);
    return reconstruct_vs_position(depth, coord);
}

vec3 gbuffer_reconstruct_vs_position(ivec2 coord) {
    return gbuffer_reconstruct_vs_position(int_coord_to_float(coord));
}

// View-Space Normal (Reconstructed)
// Returns the view space normal at a given texcoord. This tries to find
// a good fit normal, but thus is quite expensive.
// It does not include normal mapping, since it uses the depth buffer as source.
vec3 gbuffer_reconstruct_vs_normal_from_depth(vec2 coord) {
    vec2 pixel_size = 1.0 / SCREEN_SIZE;
    vec3 view_pos = gbuffer_reconstruct_vs_position(coord);

    // Do some work to find a good view normal
    vec3 dx_px = view_pos - gbuffer_reconstruct_vs_position(coord + pixel_size * vec2(1, 0));
    vec3 dx_py = view_pos - gbuffer_reconstruct_vs_position(coord + pixel_size * vec2(0, 1));

    vec3 dx_nx = gbuffer_reconstruct_vs_position(coord + pixel_size * vec2(-1, 0)) - view_pos;
    vec3 dx_ny = gbuffer_reconstruct_vs_position(coord + pixel_size * vec2(0, -1)) - view_pos;

    // TODO: Handle screen edges
    // TODO: use dFdx() / dFdy() for more efficient computation (shouldn't do much)

    // Find the closest distance in depth and use that sample
    vec3 dx_x = abs(dx_px.z) < abs(dx_nx.z) ? vec3(dx_px) : vec3(dx_nx);
    vec3 dx_y = abs(dx_py.z) < abs(dx_ny.z) ? vec3(dx_py) : vec3(dx_ny);

    return normalize(cross(dx_x, dx_y));
}

vec3 gbuffer_reconstruct_vs_normal_from_depth(ivec2 coord) {
    return gbuffer_reconstruct_vs_normal_from_depth(int_coord_to_float(coord));
}

// World-Space Normal (Reconstructed)
// See above.
vec3 gbuffer_reconstruct_ws_normal_from_depth(vec2 coord) {
    vec3 vs_normal = gbuffer_reconstruct_vs_normal_from_depth(coord);
    return vs_normal_to_ws(vs_normal);
}

vec3 gbuffer_reconstruct_ws_normal_from_depth(ivec2 coord) {
    return gbuffer_reconstruct_ws_normal_from_depth(int_coord_to_float(coord));
}


//
// Helper methods for low precision normals and depth
//

uniform sampler2D LowPrecisionDepth;
uniform sampler2D LowPrecisionHalfresDepth;
uniform sampler2D LowPrecisionNormals;
uniform sampler2D LowPrecisionHalfresNormals;

// Full-Res Depth
float gbuffer_get_linear_depth_16bit(vec2 coord) {
    return textureLod(LowPrecisionDepth, coord, 0).x;
}

float gbuffer_get_linear_depth_16bit(ivec2 coord) {
    return texelFetch(LowPrecisionDepth, coord, 0).x;
}

// Half-Res Depth
float gbuffer_get_halfres_linear_depth_16bit(vec2 coord) {
    return textureLod(LowPrecisionHalfresDepth, coord, 0).x;
}

float gbuffer_get_halfres_linear_depth_16bit(ivec2 coord) {
    return texelFetch(LowPrecisionHalfresDepth, coord, 0).x;
}

// Full-Res Low Precision Normals
vec3 gbuffer_get_normal_8bit(vec2 coord) {
    return unpack_normal_unsigned(textureLod(LowPrecisionNormals, coord, 0).xy);
}

vec3 gbuffer_get_normal_8bit(ivec2 coord) {
    return unpack_normal_unsigned(texelFetch(LowPrecisionNormals, coord, 0).xy);
}

// Half-Res Low Precision Normals
vec3 gbuffer_get_halfres_normal_8bit(vec2 coord) {
    return unpack_normal_unsigned(textureLod(LowPrecisionHalfresNormals, coord, 0).xy);
}

vec3 gbuffer_get_halfres_normal_8bit(ivec2 coord) {
    return unpack_normal_unsigned(texelFetch(LowPrecisionHalfresNormals, coord, 0).xy);
}
