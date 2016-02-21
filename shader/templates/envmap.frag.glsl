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

uniform vec3 envmapProbePosition;
uniform samplerCube DefaultEnvmap;

out vec4 result;

void main() {
    vec3 basecolor = texture(p3d_Texture0, vOutput.texcoord).xyz;
    basecolor *= mOutput.color;


    // vec3 shading_result = mix(basecolor, vec3(0), mOutput.metallic);
    vec3 shading_result = vec3(0);

    // Ambient
    vec3 view_vector = normalize(envmapProbePosition - vOutput.position);
    vec3 reflected = reflect(view_vector, vOutput.normal);

    // Specular ambient
    float spec_mip = mOutput.roughness * 7.0;
    vec3 spec_env = textureLod(DefaultEnvmap, reflected, spec_mip).rgb;
    shading_result += mix(vec3(0.04), basecolor, mOutput.metallic) * spec_env * 0.5;

    // Diffuse ambient
    int ibl_diffuse_mip = get_mipmap_count(DefaultEnvmap) - 5;
    vec3 diff_env = textureLod(DefaultEnvmap, vOutput.normal, ibl_diffuse_mip).rgb;
    shading_result += (1 - mOutput.metallic) * diff_env * basecolor;


    // Tonemapping to pack color
    shading_result = shading_result / (1.0 + shading_result);
    result = vec4(shading_result, 1);
}

