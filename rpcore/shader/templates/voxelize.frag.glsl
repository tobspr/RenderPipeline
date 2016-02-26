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

// Shader used for Voxelization, required for GI

%DEFINES%

#define IS_VOXELIZE_SHADER 1

#define USE_TIME_OF_DAY
#pragma include "render_pipeline_base.inc.glsl"
#pragma include "includes/shadows.inc.glsl"
#pragma include "includes/vertex_output.struct.glsl"
#pragma include "includes/material_output.struct.glsl"

%INCLUDES%
%INOUT%

layout(location=0) in VertexOutput vOutput;
layout(location=4) flat in MaterialOutput mOutput;

// Voxel data
uniform vec3 voxelGridPosition;
uniform writeonly image3D RESTRICT VoxelGridDest;

uniform samplerCube ScatteringIBLDiffuse;
uniform samplerCube ScatteringIBLSpecular;

uniform sampler2D p3d_Texture0;

#if HAVE_PLUGIN(scattering)
    uniform sampler2DShadow VXGISunShadowMapPCF;
    uniform mat4 VXGISunShadowMVP;
#endif

void main() {
    vec3 basecolor = texture(p3d_Texture0, vOutput.texcoord).xyz;
    basecolor *= mOutput.color;

    // Simplified ambient term

    vec3 ambient_diff = texture(ScatteringIBLDiffuse, vOutput.normal).xyz;
    vec3 ambient_spec = textureLod(ScatteringIBLSpecular, vOutput.normal, 6).xyz;

    vec3 ambient = ambient_diff * basecolor * (1 - mOutput.metallic);
    ambient += ambient_spec * basecolor * mOutput.metallic;
    ambient *= 0.1;

    vec3 shading_result = ambient;

    // Sun shading
    #if HAVE_PLUGIN(scattering)

        vec3 sun_vector = get_sun_vector();
        vec3 sun_color = get_sun_color();

        // Get sun shadow term
        vec3 biased_position = vOutput.position + vOutput.normal * 0.2;

        const float slope_bias =  1.0 * 0.02;
        const float normal_bias = 1.0 * 0.005;
        const float fixed_bias =  0.05 * 0.001;
        vec3 biased_pos = get_biased_position(
            vOutput.position, slope_bias, normal_bias, vOutput.normal, sun_vector);

        vec3 projected = project(VXGISunShadowMVP, biased_position);
        projected.z -= fixed_bias;
        float shadow_term = texture(VXGISunShadowMapPCF, projected).x;
        shading_result += saturate(dot(sun_vector, vOutput.normal)) * sun_color * shadow_term * basecolor;


    #endif

    // Tonemapping to pack color
    shading_result = shading_result / (1.0 + shading_result);

    // Get destination voxel
    const int resolution = GET_SETTING(vxgi, grid_resolution);
    const float ws_size = GET_SETTING(vxgi, grid_ws_size);
    vec3 vs_coord = (vOutput.position + vOutput.normal * 0.0 - voxelGridPosition + ws_size) / (2.0 * ws_size);
    ivec3 vs_icoord = ivec3(vs_coord * resolution + 1e-5);

    // Write voxel
    imageStore(VoxelGridDest, vs_icoord, vec4(shading_result, 1.0));
}

