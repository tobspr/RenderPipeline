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

uniform samplerCubeArray CubemapStorage;

layout(location=0) out vec4 result_spec;
layout(location=1) out vec4 result_diff;

// https://seblagarde.wordpress.com/2012/09/29/image-based-lighting-approaches-and-parallax-corrected-cubemap/
vec3 correct_parallax(vec3 cubemap_pos, float cubemap_size, Material m, out float roughness_mult) {
    vec3 bbmin = cubemap_pos - cubemap_size;
    vec3 bbmax = cubemap_pos + cubemap_size;
    vec3 direction = m.position - MainSceneData.camera_pos;
    vec3 reflected_dir = reflect(direction, m.normal);
    vec3 intersect0 = (bbmin - m.position) / reflected_dir;
    vec3 intersect1 = (bbmax - m.position) / reflected_dir;

    vec3 furthest = max(intersect0, intersect1);
    float dist = min(min(furthest.x, furthest.y), furthest.z);
    vec3 intersect_pos = m.position + reflected_dir * dist;
    roughness_mult = 0.5 * clamp(dist, 1.0, 4.0);
    roughness_mult = 1;
    return intersect_pos - cubemap_pos;
}

float get_cubemap_factor(vec3 cubemap_pos, float cubemap_size, Material m) {
    vec3 v = abs(cubemap_pos - m.position);
    float maxdist = max(v.x, max(v.y, v.z));
    // return step(maxdist, cubemap_size);
    // return 1;
    return saturate(maxdist / cubemap_size);
    // return 1 - saturate(pow(maxdist / cubemap_size, 2.0));
}

void main() {

    vec2 texcoord = get_texcoord();
    Material m = unpack_material(GBuffer, texcoord);

    if (is_skybox(m, MainSceneData.camera_pos)) {
        result_spec = vec4(0);
        result_diff = vec4(0);
        return;
    }

    int num_mips = get_mipmap_count(CubemapStorage);
    float mipmap = sqrt(m.roughness) * 12.0;
    float diff_mip = num_mips - 1;

    vec3 view_vector = normalize(MainSceneData.camera_pos - m.position);

    // TODO: Do for every cubemap
    vec3 cubemap_pos = vec3(0, 1, 2);
    float cubemap_size = 20;
    int cubemap_index = 0;
    float mip_mult = 0;
    vec3 parallax = correct_parallax(cubemap_pos, cubemap_size, m, mip_mult);
    float factor = get_cubemap_factor(cubemap_pos, cubemap_size, m);
    mipmap *= mix(1 - factor, 1.0, saturate(dot(m.normal, view_vector)));
    result_spec = textureLod(
        CubemapStorage, vec4(parallax, cubemap_index),
        clamp(mipmap * mip_mult, 0.0, num_mips - 1.0) );

    // Correct diffuse vector, instead of using just the normal
    result_diff = textureLod(
        CubemapStorage, vec4(m.normal, cubemap_index), diff_mip);

    // Renormalize
    result_spec.xyz /= max(1e-7, result_spec.w);
    result_diff.xyz /= max(1e-7, result_diff.w);

    // Apply clip factors
    float clip_factor = 1.0 - pow(factor, 32.0);
    result_spec *= clip_factor;
    result_diff *= clip_factor;

}
