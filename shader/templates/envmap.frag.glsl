#version 430

// Shader used for the environment map

%DEFINES%

#define IS_ENVMAP_SHADER 1

#define USE_TIME_OF_DAY
#pragma include "render_pipeline_base.inc.glsl"
#pragma include "includes/vertex_output.struct.glsl"
#pragma include "includes/material_output.struct.glsl"

%INCLUDES%
%INOUT%

layout(location=0) in VertexOutput vOutput;
layout(location=4) flat in MaterialOutput mOutput;

// uniform samplerCube ScatteringIBLDiffuse;
// uniform samplerCube ScatteringIBLSpecular;

uniform sampler2D p3d_Texture0;

// #if HAVE_PLUGIN(scattering)
//     uniform sampler2DShadow VXGISunShadowMapPCF;
//     uniform mat4 VXGISunShadowMVP;
// #endif

out vec4 result;

void main() {
    vec3 basecolor = texture(p3d_Texture0, vOutput.texcoord).xyz;
    basecolor *= mOutput.color;

    vec3 shading_result = basecolor;

    // Tonemapping to pack color
    shading_result = shading_result / (1.0 + shading_result);
    result = vec4(shading_result, 1);
}

