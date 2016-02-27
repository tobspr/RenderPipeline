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

#pragma include "includes/material_output.struct.glsl"
#pragma include "includes/shadows.inc.glsl"
#pragma include "includes/brdf.inc.glsl"


uniform samplerCube DefaultEnvmap;

// Samplers for the specular cubemaps
#if HAVE_PLUGIN(scattering)
    uniform samplerCube ScatteringIBLDiffuse;
    uniform samplerCube ScatteringIBLSpecular;
#endif


#if HAVE_PLUGIN(pssm)
    uniform sampler2DShadow PSSMSceneSunShadowMapPCF;
    uniform mat4 PSSMSceneSunShadowMVP;
#endif

// Applies forward shaded ambient
vec3 get_forward_ambient(vec3 basecolor, float roughness) {
    vec3 reflected = vOutput.normal;
    vec3 shading_result = vec3(0);

    #if HAVE_PLUGIN(scattering)
        // Specular ambient
        float spec_mip = get_specular_mipmap(roughness * roughness);
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
    shading_result += (1 - mOutput.metallic) * diff_env * basecolor / M_PI;

    // Emission
    shading_result *= max(0, 1 - mOutput.emissive);
    shading_result += mOutput.emissive * basecolor * 10.0;

    return shading_result;
}

// Applies the sun shading, and if the pssm plugin is activated, also the sun shadows
vec3 get_sun_shading(vec3 basecolor) {
     #if HAVE_PLUGIN(scattering)

        vec3 shading_result = vec3(0);

        vec3 sun_vector = get_sun_vector();
        vec3 sun_color = get_sun_color();

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
            float filter_radius = 1.0 / textureSize(PSSMSceneSunShadowMapPCF, 0).y;
            float shadow_term = 0;
            for(uint i = 0; i < 8; ++i) {
                vec3 offset = vec3(poisson_disk_2D_12[i] * filter_radius, 0);
                shadow_term += texture(PSSMSceneSunShadowMapPCF, projected + offset).x;
            }
            shadow_term /= 8.0;
        #else
            const float shadow_term = 1.0;
        #endif

        if (sun_vector.z >= -0.2) {
            shading_result += max(0.0, dot(sun_vector, vOutput.normal))
                              * sun_color * shadow_term * basecolor * (1 - mOutput.metallic);
        }

        return shading_result;

    #else
        return vec3(0);
    #endif
}
