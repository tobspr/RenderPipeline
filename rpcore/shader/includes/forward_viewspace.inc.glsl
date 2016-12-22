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

#pragma include "includes/brdf.inc.glsl"
#pragma include "includes/light_culling.inc.glsl"
#pragma include "includes/lighting_pipeline.inc.glsl"


#ifndef VIEWSPACE_SHADING
#error Cannot include forward_viewspace.inc.glsl when not using viewspace shading!
#endif

uniform samplerCube DefaultEnvmapSpec;
uniform samplerCube DefaultEnvmapDiff;


layout(r32i) uniform iimageBuffer ForwardFragmentCounter;
layout(rgba16f) uniform writeonly imageBuffer ForwardFragmentData;
layout(rgba16f) uniform writeonly imageBuffer ForwardFragmentDepth;
layout(r32ui) uniform uimageBuffer ForwardFragmentNext;
layout(r32ui) uniform uimage2D ForwardLinkedListHead;


vec3 get_envmap_specular(vec3 v, float mip) {
    return textureLod(DefaultEnvmapSpec, v.xzy, mip).xyz * DEFAULT_ENVMAP_BRIGHTNESS;
}

vec3 get_envmap_diffuse(vec3 n) {
    return textureLod(DefaultEnvmapDiff, n.xzy, 0).xyz * DEFAULT_ENVMAP_BRIGHTNESS;
}


vec3 get_forward_specular_abient(Material m, vec3 v) {
    vec3 reflected_dir = get_reflection_vector(m, v);
    float roughness = get_effective_roughness(m);

    // Compute angle between normal and view vector
    float NxV = clamp(-dot(m.normal, v), 1e-5, 1.0);
    float env_mipmap = get_mipmap_for_roughness(DefaultEnvmapSpec, roughness, NxV);

    // Sample default environment map
    vec3 ibl_specular = get_envmap_specular(reflected_dir, env_mipmap);

    return ibl_specular;
}


vec3 get_forward_lights(Material m, vec3 v) {
    ivec2 coord = ivec2(gl_FragCoord.xy);
    float linear_depth = get_linear_z_from_z(gl_FragCoord.z);
    ivec3 tile = get_lc_cell_index(coord, linear_depth);

    return shade_material_from_tile_buffer(m, tile, linear_depth);
}


void forward_submit_pixel(vec4 data) {
    ivec2 coord = ivec2(gl_FragCoord.xy);

    // Allocate fragment, and increment by 1 because 0 means no data
    uint fragment_index = imageAtomicAdd(ForwardFragmentCounter, 0, 1) + 1;

    // Store fragment data
    imageStore(ForwardFragmentData, int(fragment_index), data);

    // Store fragment depth
    imageStore(ForwardFragmentDepth, int(fragment_index), vec4(gl_FragCoord.z));

    // Get old list head, and exchange with new head
    uint old_head = imageAtomicExchange(ForwardLinkedListHead, coord, fragment_index);

    // Store fragment next
    imageStore(ForwardFragmentNext, int(fragment_index), uvec4(old_head));

    discard; // XXX: Figure whether just disabling depth write is faster
}
