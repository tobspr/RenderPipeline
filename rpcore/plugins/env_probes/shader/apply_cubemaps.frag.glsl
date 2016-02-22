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

#version 430

#define USE_MAIN_SCENE_DATA
#define USE_GBUFFER_EXTENSIONS
#pragma include "render_pipeline_base.inc.glsl"
#pragma include "includes/gbuffer.inc.glsl"

uniform samplerCubeArray CubemapTextures;
uniform samplerBuffer CubemapDataset;
uniform int probeCount;

layout(location=0) out vec4 result_spec;
layout(location=1) out vec4 result_diff;

struct Cubemap {
    mat4 transform;
    // int index;
};

Cubemap get_cubemap(int index) {
    Cubemap result;
    int offs = index * 4;
    vec4 data0 = texelFetch(CubemapDataset, offs);
    vec4 data1 = texelFetch(CubemapDataset, offs + 1);
    vec4 data2 = texelFetch(CubemapDataset, offs + 2);
    vec4 data3 = texelFetch(CubemapDataset, offs + 3);
    result.transform = mat4(data0, data1, data2, data3);
    return result;
}

// https://seblagarde.wordpress.com/2012/09/29/image-based-lighting-approaches-and-parallax-corrected-cubemap/
vec3 get_cubemap_vector(Cubemap map, Material m, out float factor) {
    vec3 view_vector = normalize(m.position - MainSceneData.camera_pos);
    vec3 reflected = reflect(view_vector, m.normal);

    // Intersection with OBB, convert to unit box space
    // Transform in local unit parallax cube space (scaled and rotated)
    vec3 ray_ls = (map.transform * vec4(reflected, 0)).xyz;
    vec3 position_ls = (map.transform * vec4(m.position, 1)).xyz;

    // Get fading factor
    vec3 local_v = abs(position_ls);
    factor = max(local_v.x, max(local_v.y, local_v.z));

    // Intersect with unit box
    vec3 first_plane  = (1.0 - position_ls) / ray_ls;
    vec3 second_plane = (-1.0 - position_ls) / ray_ls;
    vec3 furthest_plane = max(first_plane, second_plane);
    float dist = min(furthest_plane.x, min(furthest_plane.y, furthest_plane.z));

    // Use distance in world space directly to recover intersection
    vec3 intersection_pos = m.position + reflected * dist;
    return (map.transform * vec4(intersection_pos, 1)).xyz;
}

float apply_cubemap(int index, Material m, out vec4 diffuse, out vec4 specular) {

    float factor = 0.0;
    float mip_mult = 1.0;
    float mipmap = 0.0;
    // float mipmap = sqrt(m.roughness) * 12.0;
    int num_mips = get_mipmap_count(CubemapTextures);
    float diff_mip = num_mips - 1;

    Cubemap map = get_cubemap(index);
    vec3 direction = get_cubemap_vector(map, m, factor);
    specular = textureLod(CubemapTextures, vec4(direction, index),
        clamp(mipmap * mip_mult, 0.0, num_mips - 1.0) );
    diffuse = textureLod(CubemapTextures, vec4(m.normal, index), diff_mip);

    // Renormalize
    specular.xyz /= max(1e-7, specular.w);
    diffuse.xyz /= max(1e-7, diffuse.w);

    // Apply clip factors
    float clip_factor = saturate( (1 - factor) / 1.0);

    specular *= clip_factor;
    diffuse *= clip_factor;

    return clip_factor;
}


void main() {

    vec2 texcoord = get_texcoord();
    Material m = unpack_material(GBuffer, texcoord);

    if (is_skybox(m, MainSceneData.camera_pos)) {
        result_spec = vec4(0);
        result_diff = vec4(0);
        return;
    }

    vec4 total_diffuse = vec4(0);
    vec4 total_specular = vec4(0);
    float total_weight = 0.0;

    // [TODO] for (every cubemap) {
    for (int i = 0; i < probeCount; ++i) {
        vec4 diff, spec;
        total_weight += apply_cubemap(i, m, diff, spec);
        total_diffuse += diff;
        total_specular += spec;
    }

    total_weight = max(1e-3, total_weight);
    result_spec = total_specular / total_weight;
    result_diff = total_diffuse / total_weight;

    // result_spec.xyz = vec3(total_weight * 0.5);
    // result_spec.w = 1;
}
