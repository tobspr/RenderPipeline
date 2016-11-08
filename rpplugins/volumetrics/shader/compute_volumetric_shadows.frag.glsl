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

#define USE_TIME_OF_DAY 1
#define USE_GBUFFER_EXTENSIONS
#pragma include "render_pipeline_base.inc.glsl"
#pragma include "includes/gbuffer.inc.glsl"
#pragma include "includes/shadows.inc.glsl"
#pragma include "includes/noise.inc.glsl"

#pragma optionNV (unroll all)

uniform sampler2D ShadedScene;

#if HAVE_PLUGIN(pssm)
uniform mat4 PSSMDistSunShadowMapMVP;
uniform sampler2D PSSMDistSunShadowMap;
#endif

out vec4 result;

void main() {

    #if DEBUG_MODE
        result = vec4(0);
        return;
    #endif

    vec2 texcoord = get_half_texcoord();

    vec3 start_pos = MainSceneData.camera_pos;
    vec3 end_pos = get_gbuffer_position(GBuffer, texcoord);

    // if (is_skybox(end_pos, MainSceneData.camera_pos))
    // {
    //     result = vec4(0);
    //     return;
    // }

    float max_distance = 80.0;

    vec3 step_vector = (end_pos - start_pos);
    if (length(step_vector) > max_distance) {
        step_vector = normalize(step_vector) * max_distance;
    }

    end_pos = start_pos + step_vector;

    float jitter = rand(ivec2(gl_FragCoord.xy) % 2);


    const int num_steps = 50;
    vec3 step_offs = step_vector / num_steps;

    float volumetrics = 0.0;
    // float volume_density = 0.001 * GET_SETTING(volumetrics, volumetric_shadow_intensity);
    float volume_density = 0.0;

    vec3 sun_vector = get_sun_vector();
    vec3 sun_color = get_sun_color() * get_sun_color_scale(sun_vector);

    const float slope_bias = GET_SETTING(pssm, slope_bias) * 0.1 * 2;
    const float normal_bias = GET_SETTING(pssm, normal_bias) * 0.1;
    const float fixed_bias = 0.0005;

    for (int i = 0; i < num_steps; ++i) {

        vec3 pos = start_pos + (i + jitter) * step_offs;

        // Compute the biased position based on the normal and slope scaled
        // bias.
        vec3 biased_pos = get_biased_position(pos,
            slope_bias, normal_bias, vec3(0, 0, 1), sun_vector);
        vec3 proj = project(PSSMDistSunShadowMapMVP, biased_pos);
        proj.z -= fixed_bias;

        float shadow_term = 0;
        if (!out_of_unit_box(proj)) {
            // break;

            const float esm_factor = 5.0;
            float depth_sample = textureLod(PSSMDistSunShadowMap, proj.xy, 0).x;
            shadow_term = saturate(exp(-esm_factor * proj.z) * depth_sample);
            shadow_term = pow(shadow_term, 1e2);
        }

        volumetrics += saturate(shadow_term);
    }

    volumetrics /= float(num_steps);
    // volumetrics = 1 - volumetrics;
    // volumetrics = pow(volumetrics, 3.0);
    // volumetrics *= 3.0;
    volumetrics = saturate(volumetrics);
    // volumetrics.xyz = pow(volumetrics.xyz, vec3(2.0));
    // volumetrics *= 0.1 * sun_color;
    // volumetrics.xyz *= 0.27 * sun_color;

    result = vec4(sun_color * 0.08, 1.2) * volumetrics;
    // volumetrics.xyz = pow(volumetrics.xyz, vec3(2.0));
    // volumetrics.xyz *= sun_color;
    // volumetrics.w *= 10.0;
    // volumetrics.w = saturate(volumetrics.w);



}
