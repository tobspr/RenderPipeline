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

#version 420

#pragma optionNV (unroll all)

#define USE_MAIN_SCENE_DATA
#pragma include "render_pipeline_base.inc.glsl"
#pragma include "includes/gbuffer.inc.glsl"
#pragma include "includes/brdf.inc.glsl"

out vec4 result;

uniform sampler2D SourceTex;
uniform sampler2D MipChain;
uniform GBufferData GBuffer;

void main() {
    // Get sample coordinates
    ivec2 coord = ivec2(gl_FragCoord.xy);
    ivec2 bil_start_coord = get_bilateral_coord(coord);
    vec2 texcoord = ((bil_start_coord * 2) + 0.5) / SCREEN_SIZE;

    // Get current pixel data
    float mid_depth = get_gbuffer_depth(GBuffer, coord);
    vec3 ws_normal = get_gbuffer_normal(GBuffer, coord);

    Material m = unpack_material(GBuffer, texcoord);

    if (is_skybox(m.position)) {
        result = vec4(0);
        return;
    }

    // const float max_depth_diff = upscaleWeights.x; // 0.001
    // const float max_nrm_diff = upscaleWeights.y; // 0.001

    // const float max_depth_diff = 0.0001;
    // const float max_nrm_diff = 0.001;

    float weights = 0.0;
    vec4 accum = vec4(0);

    // Controls how many other pixels should be taken into account, besides
    // of the 4 direct neighbors.
    const int search_radius = 0;

    vec3 view_vector = normalize(m.position - MainSceneData.camera_pos);

    // Get reflection directory
    vec3 reflected_dir = get_reflection_vector(m, view_vector);

    float roughness = m.shading_model == SHADING_MODEL_CLEARCOAT ? CLEARCOAT_ROUGHNESS : m.roughness;

    // float mipmap = roughness * 32.0;

    // Accumulate all samples
    for (int x = -search_radius; x < 2 + search_radius; ++x) {
        for (int y = -search_radius; y < 2 + search_radius; ++y) {


            ivec2 source_coord = bil_start_coord + ivec2(x, y);
            // ivec2 source_coord = bil_start_coord;
            vec4 source_sample = texelFetch(SourceTex, source_coord, 0);
            float sample_depth = get_gbuffer_depth(GBuffer, source_coord * 2);

            // Skip empty samples
            if (source_sample.x*source_sample.x + source_sample.y*source_sample.y < 1e-2) {
                continue;
            }

            // Get start view pos
            vec2 offcoord = ((source_coord * 2) + 0.5) / SCREEN_SIZE;
            // vec3 wp_sample = calculate_surface_pos(sample_depth, offcoord);

            // Get end view pos
            float intersection_depth = get_gbuffer_depth(GBuffer, source_sample.xy);
            vec3 wp_dest_sample = calculate_surface_pos(intersection_depth, source_sample.xy);

            vec3 direction_to_sample = normalize(wp_dest_sample - m.position);
            vec3 h = normalize(-view_vector + direction_to_sample);
            float angle = saturate(dot(m.normal, h));

            float weight = 1;
            weight *= clamp(brdf_distribution_ggx(angle, 0.1), 1e-5, 100.0);

            // result = vec4(saturate(dot(m.normal, h)));
            // result = vec4(h, 1);
            // return;
            // weight *= brdf_distribution_ggx(angle, roughness);

            // weight = saturate(dot(reflected_dir, view_vector));
            // weight = 1;
            // result.xyz = vec3(weight);

            // float mipmap = saturate(dot(reflected_dir, m.normal)) * 7.0;
            float mipmap = 1;


            vec4 color_sample = textureLod(MipChain, source_sample.xy, mipmap);
            color_sample *= saturate(2.0 * dot(reflected_dir, view_vector));

            // Check how much information those pixels share, and if it is
            // enough, use that sample
            // vec3 sample_nrm = get_gbuffer_normal(GBuffer, source_coord * 2);
            // float depth_diff = abs(sample_depth - mid_depth) / max_depth_diff;
            // float nrm_diff = max(0, dot(sample_nrm, mids_nrm));
            // float weight = 1.0 - saturate(depth_diff);
            // weight *= pow(nrm_diff, 1.0 / max_nrm_diff);

            // if (useZAsWeight) {
            //     weight *= source_sample.w;
            // }

            // Make sure we don't have a null-weight, but instead only a very
            // small weight, so that in case no pixel matches, we still have
            // data to work with.
            // weight = max(1e-5, weight);
            // weight *= color_sample.w;

            accum += color_sample * weight;
            weights += weight;
        }
    }

    if (weights < 1e-5) {
        // When no sample was valid, take the center sample - this is still
        // better than invalid pixels
        // result = texelFetch(SourceTex, coord / 2, 0);
        // result = vec4(1, 0, 0, 1);
        accum = vec4(0);
        // return;
    } else {
        // result = accum / weights;
        accum /= weights;
    }



    // result = vec4(vp_center, 1);
    result = vec4(accum);
    // result.w = 1;
    // result = texelFetch(SourceTex, coord / 2, 0);

}
