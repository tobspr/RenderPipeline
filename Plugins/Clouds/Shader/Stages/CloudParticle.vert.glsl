/**
 * 
 * RenderPipeline
 * 
 * Copyright (c) 2014-2015 tobspr <tobias.springer1@gmail.com>
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

in vec4 p3d_Vertex;
out vec2 texcoord;
out vec4 cloudcolor;

uniform sampler3D CloudVoxels;

uniform mat4 p3d_ProjectionMatrix;
uniform mat4 p3d_ViewMatrix;

void main() {
    texcoord = p3d_Vertex.xz * 0.5 + 0.5;
    texcoord = texcoord * 0.25;

    int instance_id = gl_InstanceID;
    int v_x = instance_id % CLOUD_RES_XY;
    int v_y = (instance_id / CLOUD_RES_XY) % CLOUD_RES_XY;
    int v_z = instance_id  / (CLOUD_RES_XY * CLOUD_RES_XY);

    // texcoord += vec2(instance_id % 4, (instance_id / 4) % 4) / 4.0;

    const vec3 cloud_start = vec3(-3500, -3500, 500);
    const vec3 cloud_end = vec3(3500, 3500, 1000);

    vec3 voxcoord = vec3(v_x, v_y, v_z) / vec3(CLOUD_RES_XY, CLOUD_RES_XY, CLOUD_RES_Z);
    cloudcolor = texture(CloudVoxels, voxcoord + 0.5 / vec3(CLOUD_RES_XY, CLOUD_RES_XY, CLOUD_RES_Z));


    vec3 offset = voxcoord * (cloud_end - cloud_start) + cloud_start;
    if (cloudcolor.w < 0.01) {
        gl_Position = vec4(0);
        return;
    }   

    vec4 vtx_pos = p3d_Vertex;
    vtx_pos.xyz *= 70.0;

    vec4 off_proj = p3d_ViewMatrix * vec4(offset, 1);
    vec4 vtx_proj = MainSceneData.view_mat_billboard * vtx_pos;
    gl_Position = p3d_ProjectionMatrix * (off_proj + vtx_proj);
}
