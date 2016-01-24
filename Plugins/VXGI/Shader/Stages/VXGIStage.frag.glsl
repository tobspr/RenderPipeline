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

#version 400

#define USE_MAIN_SCENE_DATA
#pragma include "Includes/Configuration.inc.glsl"
#pragma include "Includes/GBuffer.inc.glsl"
#pragma include "Includes/PoissonDisk.inc.glsl"

uniform vec3 voxelGridPosition;
uniform float voxelGridSize;
uniform int voxelGridResolution;

uniform sampler3D SceneVoxels;
uniform sampler2D ShadedScene;

uniform samplerCube ScatteringIBLSpecular;
uniform samplerCube ScatteringIBLDiffuse;

uniform GBufferData GBuffer;

layout(location=0) out vec4 specular_result;
layout(location=1) out vec4 diffuse_result;



vec4 trace_cone(vec3 start_pos, vec3 direction, bool is_specular, float cone_grow_factor) {

    const int max_steps = 20;
    float cone_radius = (1.0 + 10.0 * cone_grow_factor) / GET_SETTING(VXGI, grid_resolution);
    start_pos += direction * cone_radius * 0.5;
    vec3 current_pos = start_pos;
    vec4 accum = vec4(0);
    float mipmap = 0.0;
    for (int i = 0; i < max_steps; ++i) {
        mipmap = log2(cone_radius * GET_SETTING(VXGI, grid_resolution));
        vec4 sampled = textureLod(SceneVoxels, current_pos, mipmap);
        accum += sampled * (1.0 - accum.w);
        current_pos += direction * cone_radius / 1.7;
        cone_radius *= 1.0 + cone_grow_factor;
    }

    accum.xyz = accum.xyz / (1 - accum.xyz);
    accum.xyz *= 1.5;

    if (is_specular) {
        accum.xyz += textureLod(ScatteringIBLSpecular, direction, mipmap).xyz * (1-accum.w);
    } else {
        accum.xyz += texture(ScatteringIBLDiffuse, direction).xyz * (1-accum.w);
    }

    return accum;
}

void main() {

    Material m = unpack_material(GBuffer);

    // Get voxel space coordinate
    vec3 voxel_coord = (m.position - voxelGridPosition) / GET_SETTING(VXGI, grid_ws_size);
    voxel_coord = fma(voxel_coord, vec3(0.5), vec3(0.5));

    // Get view vector
    vec3 view_vector = normalize(MainSceneData.camera_pos - m.position);
    vec3 reflected_dir = reflect(-view_vector, m.normal);


    if (voxel_coord.x < 0.0 || voxel_coord.y < 0.0 || voxel_coord.z < 0.0 ||
        voxel_coord.x > 1.0 || voxel_coord.y > 1.0 || voxel_coord.z > 1.0)
    {
        specular_result = textureLod(ScatteringIBLSpecular, reflected_dir, 7) * 0.3;
        diffuse_result = texture(ScatteringIBLDiffuse, m.normal);
        return;
    }

    // Trace specular cone
    vec4 specular_cone = trace_cone(voxel_coord, reflected_dir, true, m.roughness * 0.2);

    specular_result = vec4(specular_cone.xyz, 1.0);

    // Trace diffuse cones
    vec4 diffuse_accum = vec4(0);

    for (int i = 0; i < 16; ++i) {
        vec3 direction = poisson_disk_3D_16[i];
        direction = faceforward(direction, direction, -m.normal);
        float weight = dot(m.normal, direction); // Guaranteed to be > 0
        vec4 cone = trace_cone(voxel_coord, direction, false, 0.2);
        diffuse_accum.xyz += cone.xyz * weight;
        diffuse_accum.w += weight;
    }

    diffuse_accum /= diffuse_accum.w;
    diffuse_result = diffuse_accum;
}

