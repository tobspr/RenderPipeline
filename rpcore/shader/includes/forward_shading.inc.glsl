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

#pragma include "includes/shadows.inc.glsl"
#pragma include "includes/brdf.inc.glsl"
#pragma include "includes/lights.inc.glsl"
#pragma include "includes/light_data.inc.glsl"

uniform samplerCube DefaultEnvmap;
uniform samplerBuffer AllLightsData;
uniform int maxLightIndex;

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
vec3 get_forward_ambient(MaterialBaseInput mInput, vec3 basecolor) {
    vec3 reflected = vOutput.normal;
    vec3 shading_result = vec3(0);

    #if HAVE_PLUGIN(scattering)
        vec3 diff_env = textureLod(ScatteringIBLDiffuse, vOutput.normal, 0).rgb;

    #else
        int ibl_diffuse_mip = get_mipmap_count(DefaultEnvmap) - 5;
        vec3 diff_env = textureLod(DefaultEnvmap, vOutput.normal, ibl_diffuse_mip).rgb * DEFAULT_ENVMAP_BRIGHTNESS;
    #endif

    shading_result += (0.5 + 0.5 * basecolor);

    // Emission
    if (mInput.shading_model == SHADING_MODEL_EMISSIVE) {
        shading_result = basecolor * (0.005 + diff_env) * 30.0;
    }

    return shading_result;
}

// Applies the sun shading, and if the pssm plugin is activated, also the sun shadows
vec3 get_sun_shading(MaterialBaseInput mInput, vec3 basecolor) {

     #if HAVE_PLUGIN(scattering)

        vec3 shading_result = vec3(0);

        vec3 sun_vector = get_sun_vector();
        vec3 sun_color = get_sun_color() * get_sun_color_scale(sun_vector);

        // Get sun shadow term
        #if HAVE_PLUGIN(pssm)
            vec3 biased_position = vOutput.position + vOutput.normal * 0.2;

            const float slope_bias =  0.3 * 0.02;
            const float normal_bias = 0.0 * 0.005;
            const float fixed_bias =  0.5 * 0.001;
            vec3 biased_pos = get_biased_position(
                vOutput.position, slope_bias, normal_bias, vOutput.normal, sun_vector);

            vec3 projected = project(PSSMSceneSunShadowMVP, biased_position);
            projected.z -= fixed_bias;

            // Fast shadow filtering
            float filter_radius = 1.0 / textureSize(PSSMSceneSunShadowMapPCF, 0).y;
            float shadow_term = 0;
            for(uint i = 0; i < 12; ++i) {
                vec3 offset = vec3(poisson_disk_2D_12[i] * filter_radius, 0);
                shadow_term += texture(PSSMSceneSunShadowMapPCF, projected + offset).x;
            }
            shadow_term /= 12.0;
        #else
            const float shadow_term = 1.0;
        #endif

        if (sun_vector.z >= SUN_VECTOR_HORIZON) {
            float NxL = saturate(dot(sun_vector, vOutput.normal));
            shading_result += NxL * sun_color * shadow_term * basecolor;
        }

        return shading_result;

    #else
        return vec3(0);
    #endif
}

vec3 get_forward_light_shading(vec3 basecolor) {

    vec3 shading_result = vec3(0);

    for (int i = 0; i <= maxLightIndex; ++i) {
        LightData light_data = read_light_data(AllLightsData, i * 4);
        int light_type = get_light_type(light_data);

        // Skip Null-Lights
        if (light_type < 1) continue;

        vec3 light_pos = get_light_position(light_data);
        vec3 l = light_pos - vOutput.position;
        float l_len = length(l);
        vec3 light_color = get_light_color(light_data);

        // Shade depending on light type
        switch(light_type) {
            case LT_POINT_LIGHT: {
                float radius = get_pointlight_radius(light_data);
                float inner_radius = get_pointlight_inner_radius(light_data);
                float att = attenuation_curve(dot(l, l), radius);
                float NxL = saturate(dot(vOutput.normal, l) / l_len);
                shading_result += saturate(att) * NxL * (basecolor * light_color);
                break;
            }

            case LT_SPOT_LIGHT: {
                float radius    = get_spotlight_radius(light_data);
                float fov       = get_spotlight_fov(light_data);
                vec3 direction  = get_spotlight_direction(light_data);

                float att = get_spotlight_attenuation(l / l_len, direction,
                    fov, radius, dot(l, l), -1);
                float NxL = saturate(dot(vOutput.normal, l) / l_len);
                shading_result += saturate(att) * NxL * (basecolor * light_color);
                break;
            }

        }

    }

    return shading_result / M_PI;
}
