#version 430

// Shader used for the environment map

%DEFINES%

#define IS_ENVMAP_SHADER 1

#define USE_TIME_OF_DAY
#pragma include "render_pipeline_base.inc.glsl"
#pragma include "includes/shadows.inc.glsl"
#pragma include "includes/poisson_disk.inc.glsl"
#pragma include "includes/vertex_output.struct.glsl"
#pragma include "includes/material_output.struct.glsl"

%INCLUDES%
%INOUT%

layout(location=0) in VertexOutput vOutput;
layout(location=4) flat in MaterialOutput mOutput;

#if HAVE_PLUGIN(scattering)
    uniform samplerCube ScatteringIBLDiffuse;
    uniform samplerCube ScatteringIBLSpecular;
#endif

uniform sampler2D p3d_Texture0;

#if HAVE_PLUGIN(pssm)
    uniform sampler2DShadow PSSMSceneSunShadowMapPCF;
    uniform mat4 PSSMSceneSunShadowMVP;
#endif

uniform samplerCube DefaultEnvmap;

out vec4 result;

void main() {
    vec3 basecolor = texture(p3d_Texture0, vOutput.texcoord).xyz;
    basecolor *= mOutput.color;


    // vec3 shading_result = mix(basecolor, vec3(0), mOutput.metallic);
    vec3 shading_result = vec3(0);

    // Ambient
    vec3 reflected = vOutput.normal;

    #if HAVE_PLUGIN(scattering)
        // Specular ambient
        float spec_mip = max(1, mOutput.roughness * 5.0);
        vec3 spec_env = textureLod(ScatteringIBLSpecular, reflected, spec_mip).rgb;

        // Diffuse ambient
        vec3 diff_env = textureLod(ScatteringIBLDiffuse, vOutput.normal, 0).rgb;

    #else
        // Specular ambient
        float spec_mip = max(3, mOutput.roughness * 7.0);
        vec3 spec_env = textureLod(DefaultEnvmap, reflected, spec_mip).rgb;

        // Diffuse ambient
        int ibl_diffuse_mip = get_mipmap_count(DefaultEnvmap) - 5;
        vec3 diff_env = textureLod(DefaultEnvmap, vOutput.normal, ibl_diffuse_mip).rgb;

    #endif

    shading_result += mix(vec3(0.04), basecolor, mOutput.metallic) * spec_env;
    shading_result += (1 - mOutput.metallic) * diff_env * basecolor;


    // Sun shading
    #if HAVE_PLUGIN(scattering)

        vec3 sun_vector = sun_azimuth_to_angle(
            TimeOfDay.scattering.sun_azimuth,
            TimeOfDay.scattering.sun_altitude);

        vec3 sun_color = TimeOfDay.scattering.sun_color / 255.0 *
            TimeOfDay.scattering.sun_intensity * 20.0;

        // Get sun shadow term
        #if HAVE_PLUGIN(pssm)
            vec3 biased_position = vOutput.position + vOutput.normal * 0.2;

            const float slope_bias =  1.0 * 0.02;
            const float normal_bias = 1.0 * 0.005;
            const float fixed_bias =  0.05 * 0.001;
            vec3 biased_pos = get_biased_position(
                vOutput.position, slope_bias, normal_bias, vOutput.normal, sun_vector);

            vec3 projected = project(PSSMSceneSunShadowMVP, biased_position);
            projected.z -= fixed_bias;

            // Fast shadow filtering
            float filter_radius = 2.0 / textureSize(PSSMSceneSunShadowMapPCF, 0).x;
            float shadow_term = 0;
            for(uint i = 0; i < 8; ++i) {
                vec3 offset = vec3(poisson_disk_2D_12[i] * filter_radius, 0);
                shadow_term += texture(PSSMSceneSunShadowMapPCF, projected + offset).x;
            }
            shadow_term /= 8.0;
        #else
            const float shadow_term = 1.0;
        #endif

        if (sun_vector.z > 0) {
            shading_result += max(0.0, dot(sun_vector, vOutput.normal))
                              * sun_color * shadow_term * basecolor * (1 - mOutput.metallic);
        }

    #endif

    result = vec4(shading_result, 1);
}

