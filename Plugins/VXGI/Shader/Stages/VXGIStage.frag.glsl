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

uniform vec3 voxelGridPosition;
uniform float voxelGridSize;
uniform int voxelGridResolution;

uniform sampler3D SceneVoxels;
uniform sampler2D ShadedScene;

uniform samplerCube ScatteringIBLSpecular;

uniform GBufferData GBuffer;
out vec4 result;



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
        result = texture(ScatteringIBLSpecular, reflected_dir);
        return;
    }

    vec3 specular_gi = vec3(0);


    // Trace specular cone
    vec3 start_pos = voxel_coord;
    vec3 end_pos = start_pos + reflected_dir * 0.5;
    vec3 current_pos = start_pos + reflected_dir * 2.0 / GET_SETTING(VXGI, grid_resolution);

    const int num_steps = 256;
    vec3 trace_step = (end_pos - start_pos) / num_steps;
    vec4 accum = vec4(0.0);
    for (int i = 0; i < num_steps; ++i) {
        vec4 sampled = textureLod(SceneVoxels, current_pos, 0);
        accum += sampled * (1.0 - accum.w);
        current_pos += trace_step;
    }

    accum.xyz = accum.xyz / (1 - accum.xyz);
    // accum.xyz *= 0.1;

    accum.xyz += texture(ScatteringIBLSpecular, reflected_dir).xyz * (1-accum.w);

    result = vec4(accum.xyz, 1.0);

}
