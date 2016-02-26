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
#define USE_TIME_OF_DAY
#pragma include "render_pipeline_base.inc.glsl"
#pragma include "includes/transforms.inc.glsl"
#pragma include "includes/gbuffer.inc.glsl"
#pragma include "includes/lighting_pipeline.inc.glsl"
#pragma include "includes/poisson_disk.inc.glsl"
#pragma include "includes/shadows.inc.glsl"
#pragma include "includes/skin_shading.inc.glsl"

out vec4 result;

uniform GBufferData GBuffer;
uniform sampler2D ShadedScene;

#if GET_SETTING(pssm, use_pcf)
    uniform sampler2DShadow PSSMShadowAtlasPCF;
#endif

uniform sampler2D PSSMShadowAtlas;

uniform mat4 pssm_mvps[GET_SETTING(pssm, split_count)];
uniform vec2 pssm_nearfar[GET_SETTING(pssm, split_count)];
uniform vec3 pssm_sun_vector;

#if HAVE_PLUGIN(clouds)
uniform sampler3D CloudVoxels;
#endif


vec2 get_split_coord(vec2 local_coord, int split_index) {
    local_coord.x = (local_coord.x + split_index) / float(GET_SETTING(pssm, split_count));
    return local_coord;
}

float get_shadow(vec2 coord, float refz) {
    #if GET_SETTING(pssm, use_pcf)
        return textureLod(PSSMShadowAtlasPCF, vec3(coord, refz), 0);
    #else
        float depth_sample = textureLod(PSSMShadowAtlas, coord, 0).x;
        return step(refz, depth_sample);
    #endif
}


void main() {

    vec3 sun_vector = get_sun_vector();
    vec3 sun_color = get_sun_color();

    // Get current scene color
    ivec2 coord = ivec2(gl_FragCoord.xy);
    vec4 scene_color = texelFetch(ShadedScene, coord, 0);

    // Get the material data
    Material m = unpack_material(GBuffer);

    // Early out, different optimizations
    bool early_out = is_skybox(m);
    early_out = early_out || sun_vector.z < 0.0;
    early_out = early_out || dot(m.normal, sun_vector) < 0.0;

    if (early_out) {
        result = scene_color;
        return;
    }

    // Variables to accumulate the shadows
    float shadow_factor = 1.0;
    vec3 lighting_result = vec3(0);
    vec3 transmittance = vec3(1);

    // Find lowest split in range
    const int split_count = GET_SETTING(pssm, split_count);
    int split = 99;
    float border_bias = 1 - (1.0 / (1.0 + GET_SETTING(pssm, border_bias)));
    border_bias *= 0.5;

    // Find the first matching split
    for (int i = 0; i < split_count; ++i) {
        vec3 coord = project(pssm_mvps[i], m.position);
        if (coord.x >= border_bias && coord.x <= 1-border_bias &&
            coord.y >= border_bias && coord.y <= 1-border_bias &&
            coord.z >= 0.0 && coord.z <= 1.0) {
            split = i;
            break;
        }
    }

    // Compute the shadowing factor
    if (split < GET_SETTING(pssm, split_count)) {

        // Get the MVP for the current split
        mat4 mvp = pssm_mvps[split];

        // Get the plugin settings
        const float slope_bias = GET_SETTING(pssm, slope_bias) * 0.05;
        const float normal_bias = GET_SETTING(pssm, normal_bias) * 0.005;
        const float fixed_bias = GET_SETTING(pssm, fixed_bias) * 0.001;
        const int num_samples = GET_SETTING(pssm, filter_sample_count);
        const float filter_radius = GET_SETTING(pssm, filter_radius) / GET_SETTING(pssm, resolution);


        // Compute the biased position based on the normal and slope scaled
        // bias.
        vec3 biased_pos = get_biased_position(m.position,
            slope_bias, normal_bias, m.normal, sun_vector);

        // Project the current pixel to the view of the light
        vec3 projected = project(mvp, biased_pos);
        vec2 projected_coord = get_split_coord(projected.xy, split);

        // Compute the fixed bias
        float ref_depth = projected.z - fixed_bias;

        // Find filter size
        vec2 filter_size = find_filter_size(mvp, sun_vector, filter_radius);

        #if GET_SETTING(pssm, use_pcss)

            {
            /*

                PCSS Kernel

                Scan the region of the pixel for blockers, penumbra size is
                amount of blockers compared to non-blockers.

            */

            const int num_search_samples = GET_SETTING(pssm, pcss_search_samples);

            float num_blockers = 0.0;
            float sum_blockers = 0.0;

            for (int i = 0; i < num_search_samples; ++i) {

                // Find random sample locations on a poisson disk
                vec2 offset = poisson_disk_2D_32[i];

                // Find depth at sample location
                float sampled_depth = textureLod(PSSMShadowAtlas,
                    projected_coord + offset * filter_size * 10.0, 0).x;

                // Compare the depth with the pixel depth, in case its smaller,
                // we found a blocker
                float factor = step(sampled_depth, ref_depth);
                num_blockers += factor;
                sum_blockers += sampled_depth * factor;
            }

            // Examine ratio between blockers and non-blockers
            float avg_blocker_depth = sum_blockers / num_blockers;

            // Penumbra size also takes average blocker depth into account
            float penumbra_size = max(0.002, ref_depth - avg_blocker_depth) /
                ref_depth * GET_SETTING(pssm, pcss_penumbra_size);

            // Apply penumbra size
            filter_size *= penumbra_size;

            }

        #endif

        shadow_factor = 0.0;

        // Do the actual shadow map filtering
        for (int i = 0; i < num_samples; ++i) {

            // Get sample from a random poisson disk
            vec2 offset = poisson_disk_2D_32[i];

            // Find depth and apply contribution
            shadow_factor += get_shadow(
                projected_coord + offset * filter_size, ref_depth);
        }

        // Normalize shadow factor
        shadow_factor /= num_samples;

        // Scale the shadow factor a bit, artistic choice
        // shadow_factor = shadow_factor * (1.3) -  0.3;

        shadow_factor = saturate(shadow_factor);


        // skin shading, use a single tap
        BRANCH_TRANSLUCENCY(m)

            // Get the current split near and far planes
            vec2 split_near_far = pssm_nearfar[split];

            // Bias to move the position "into" the object, prevents artifacts
            float skin_border_factor = 0.005;

            // Project the biased position to light space
            vec3 projected_skin = project(mvp, m.position - m.normal * skin_border_factor);
            vec2 projected_skin_coord = get_split_coord(projected_skin.xy, split);
            float skin_ref_depth = projected_skin.z;

            // Get the shadow sample
            float shadow_sample = textureLod(PSSMShadowAtlas, projected_skin_coord, 0).x;

            // Reconstruct intersection position
            // TODO: This is totally slow! Pass it as input
            mat4 inverse_mvp = inverse(mvp);
            vec3 intersection_pos = calculate_surface_pos_ortho(shadow_sample, projected_skin.xy, split_near_far.x, split_near_far.y, inverse_mvp);

            // Get the distance the light traveled through the medium
            float distance_through_medium = distance(m.position, intersection_pos.xyz);

            // TODO: Maybe we can remove this branch
            if (skin_ref_depth < shadow_sample) distance_through_medium = 0.0;

            // Fetch the skin transmittance
            transmittance = skin_transmittance(distance_through_medium);

        END_BRANCH_TRANSLUCENCY()
    }

    // Raymarch clouds
    // CloudVoxels
    #if HAVE_PLUGIN(clouds)
        {
        vec3 start_coord = vec3(m.position.xy / 800.0, 0);
        vec3 end_coord = start_coord + vec3(0, 0, 1);
        const int num_steps = 32;
        vec3 step_dir = (end_coord - start_coord) / num_steps;
        float cloud_factor = 0.0;
        for (int i = 0; i < num_steps; ++i) {
            float cloud_sample = texture(CloudVoxels, start_coord).w;
            cloud_factor += cloud_sample;
            start_coord += step_dir;
        }
        cloud_factor /= num_steps;
        cloud_factor *= 10.0;
        shadow_factor *= saturate(1.0 - cloud_factor);

        }
    #endif

    // Compute the sun lighting
    vec3 v = normalize(MainSceneData.camera_pos - m.position);
    vec3 l = sun_vector;
    lighting_result = apply_light(m, v, l, sun_color, 1.0, shadow_factor, vec4(0), transmittance, 0.0005);

    #if DEBUG_MODE
        lighting_result *= 0;
    #endif

    #if MODE_ACTIVE(PSSM_SPLITS)
        float factor = float(split) / GET_SETTING(pssm, split_count);
        lighting_result = saturate(shadow_factor+0.5) * vec3(factor, 1 - factor, 0);
    #endif

    result = scene_color + vec4(lighting_result, 0);
}