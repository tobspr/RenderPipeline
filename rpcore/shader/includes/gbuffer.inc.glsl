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

#pragma include "includes/material.inc.glsl"
#pragma include "includes/normal_packing.inc.glsl"
#pragma include "includes/brdf.inc.glsl"

/*

GBuffer - Unpacking

*/

#pragma include "includes/transforms.inc.glsl"

// Common gbuffer data
struct GBufferData {
    sampler2D Depth;
    sampler2D Data0;
    sampler2D Data1;
    sampler2D Data2;
};

#warning Please use the new gbuffer2.inc.glsl include!

// Checks whether the given material is the skybox
bool is_skybox(vec3 pos, vec3 camera_pos) {
    return distance(pos, camera_pos) > SKYBOX_DIST;
}

bool is_skybox(Material m, vec3 camera_pos) {
    return is_skybox(m.position, camera_pos);
}

bool is_skybox(Material m) { return is_skybox(m, MainSceneData.camera_pos); }
bool is_skybox(vec3 pos) { return is_skybox(pos, MainSceneData.camera_pos); }

// Returns the depth at a given texcoord
float get_gbuffer_depth(GBufferData data, vec2 coord) {
    return textureLod(data.Depth, coord, 0).x;
}

// Returns the depth at a given texcoord
float get_gbuffer_depth(GBufferData data, ivec2 coord) {
    return texelFetch(data.Depth, coord, 0).x;
}

// Returns the world space position at a given texcoord
vec3 get_gbuffer_position(GBufferData data, vec2 coord) {
    float depth = get_gbuffer_depth(data, coord);
    return reconstruct_ws_position(depth, coord);
}

// Returns the world space position at a given texcoord
vec3 get_gbuffer_position(GBufferData data, ivec2 coord) {
    float depth = get_gbuffer_depth(data, coord);
    vec2 tcoord = (coord + 0.5) / SCREEN_SIZE;
    return reconstruct_ws_position(depth, tcoord);
}


// Returns the world space normal at a given texcoord
vec3 get_gbuffer_normal(GBufferData data, vec2 coord) {
    vec2 packed_normal = textureLod(data.Data1, coord, 0).xy;
    return unpack_normal_octahedron(packed_normal);
}
// Returns the world space normal at a given texcoord
vec3 get_gbuffer_normal(GBufferData data, ivec2 coord) {
    vec2 packed_normal = texelFetch(data.Data1, coord, 0).xy;
    return unpack_normal_octahedron(packed_normal);
}

// Returns the velocity at a given coordinate
vec2 get_gbuffer_object_velocity(GBufferData data, vec2 coord) {
    return textureLod(data.Data2, coord, 0).xy;
}

// Returns the velocity at a given coordinate
vec2 get_gbuffer_object_velocity(GBufferData data, ivec2 coord) {
    return texelFetch(data.Data2, coord, 0).xy;
}

int get_gbuffer_shading_model(GBufferData data, vec2 coord) {
    return int(textureLod(data.Data2, coord, 0).z);
}

float get_gbuffer_roughness(GBufferData data, vec2 coord) {
    // XXX: take clearcoat into account
    return square(clamp(textureLod(data.Data0, coord, 0).w, MINIMUM_ROUGHNESS, 1.0));
}

float get_gbuffer_roughness(GBufferData data, ivec2 coord) {
    // XXX: take clearcoat into account
    return square(clamp(texelFetch(data.Data0, coord, 0).w, MINIMUM_ROUGHNESS, 1.0));
}

// Unpacks a material from the gbuffer
Material unpack_material(GBufferData data, vec2 fcoord) {

    // Fetch data from data-textures
    vec4 data0 = textureLod(data.Data0, fcoord, 0);
    vec4 data1 = textureLod(data.Data1, fcoord, 0);
    vec4 data2 = textureLod(data.Data2, fcoord, 0);

    Material m;
    m.position = get_gbuffer_position(data, fcoord);
    m.basecolor = data0.xyz;
    m.linear_roughness = clamp(data0.w, MINIMUM_ROUGHNESS, 1.0);
    m.roughness = m.linear_roughness * m.linear_roughness;
    m.normal = unpack_normal_octahedron(data1.xy);
    m.metallic = saturate(data1.z * 1.001 - 0.0005);
    m.specular_ior = data1.w;
    m.specular = ior_to_specular(data1.w);
    m.shading_model = int(data2.z);
    m.shading_model_param0 = data2.w;


    // Velocity, not stored in the Material struct but stored in the G-Buffer
    // vec2 velocity = data2.xy;
    return m;
}

// Unpacks a material from the gbuffer
Material unpack_material(GBufferData data) {
    vec2 fcoord = get_texcoord();
    return unpack_material(data, fcoord);
}

#ifdef USE_GBUFFER_EXTENSIONS

    /*

    GBuffer extensions for reading gbuffer values without having to specify
    the gbuffer.

    */

    uniform GBufferData GBuffer;

    // Returns the depth at a given texcoord
    float get_depth_at(vec2 coord) {
        return get_gbuffer_depth(GBuffer, coord);
    }
    // Returns the depth at a given texcoord
    float get_depth_at(ivec2 coord) {
        return get_gbuffer_depth(GBuffer, coord);
    }

    // Returns the view space position at a given texcoord
    vec3 get_view_pos_at(vec2 coord) {
        return reconstruct_vs_position(get_depth_at(coord), coord);
    }

    // Returns the world space position at a given texcoord
    vec3 get_world_pos_at(vec2 coord) {
        return reconstruct_ws_position(get_depth_at(coord), coord);
    }

    // Returns the velocity given texcoord
    vec2 get_object_velocity_at(vec2 coord) {
        return get_gbuffer_object_velocity(GBuffer, coord);
    }
    // Returns the velocity given texcoord
    vec2 get_object_velocity_at(ivec2 coord) {
        return get_gbuffer_object_velocity(GBuffer, coord);
    }

    // Returns the view space normal at a given texcoord. This tries to find
    // a good fit normal, but thus is quite expensive.
    // It does not include normal mapping, since it uses the depth buffer as source.
    vec3 get_view_normal_from_depth(vec2 coord) {
        vec2 pixel_size = 1.0 / SCREEN_SIZE;
        vec3 view_pos = get_view_pos_at(coord);

        // Do some work to find a good view normal
        vec3 dx_px = view_pos - get_view_pos_at(coord + pixel_size * vec2(1, 0));
        vec3 dx_py = view_pos - get_view_pos_at(coord + pixel_size * vec2(0, 1));

        vec3 dx_nx = get_view_pos_at(coord + pixel_size * vec2(-1, 0)) - view_pos;
        vec3 dx_ny = get_view_pos_at(coord + pixel_size * vec2(0, -1)) - view_pos;

        // TODO: Handle screen edges
        // Find the closest distance in depth
        vec3 dx_x = abs(dx_px.z) < abs(dx_nx.z) ? vec3(dx_px) : vec3(dx_nx);
        vec3 dx_y = abs(dx_py.z) < abs(dx_ny.z) ? vec3(dx_py) : vec3(dx_ny);

        return normalize(cross(dx_x, dx_y));
    }

    vec3 get_view_normal(vec2 coord) {

        // OPTIONAL: Just recover it from the world space normal.
        // This has the advantage that it does include normal mapping.
        #if 1
            vec3 world_normal = get_gbuffer_normal(GBuffer, coord);
            return world_normal_to_view(world_normal);
        #endif

        return get_view_normal_from_depth(coord);
    }

    vec3 get_world_normal_from_depth(vec2 coord) {
        return vs_normal_to_ws(get_view_normal_from_depth(coord));
    }

    // Returns the view space normal at a given texcoord. This approximates
    // the normal instead of calculating it accurately, thus might produce
    // smaller artifacts at edges. However you should prefer this method
    // wherever possible. It does not include normal mapping, since it uses
    // the depth buffer as source.
    vec3 get_view_normal_approx(vec2 coord) {
        vec3 view_pos = get_view_pos_at(coord);
        vec2 pixel_size = 1.0 / SCREEN_SIZE;
        vec3 dx_x = view_pos - get_view_pos_at(coord + pixel_size * vec2(1, 0));
        vec3 dx_y = view_pos - get_view_pos_at(coord + pixel_size * vec2(0, 1));
        return normalize(cross(dx_x, dx_y));
    }

#endif
