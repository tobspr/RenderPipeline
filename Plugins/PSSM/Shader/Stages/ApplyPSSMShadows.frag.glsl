#version 400

#pragma optionNV (unroll all)

#pragma include "Includes/Configuration.inc.glsl"
#pragma include "Includes/PositionReconstruction.inc.glsl"
#pragma include "Includes/GBuffer.inc.glsl"
#pragma include "Includes/LightingPipeline.inc.glsl"
#pragma include "Includes/PoissonDisk.inc.glsl"
#pragma include "Includes/Shadows.inc.glsl"

out vec4 result;

uniform GBufferData GBuffer;
uniform sampler2D ShadedScene;

#if GET_SETTING(PSSM, use_pcf)
    uniform sampler2DShadow PSSMShadowAtlasPCF;
#endif

uniform sampler2D PSSMShadowAtlas;

uniform mat4 pssm_mvps[GET_SETTING(PSSM, split_count)];
uniform float pssm_rotations[GET_SETTING(PSSM, split_count)];
uniform vec3 pssm_sun_vector;


vec2 get_split_coord(vec2 local_coord, int split_index) {
    local_coord.x = (local_coord.x + split_index) / float(GET_SETTING(PSSM, split_count));
    return local_coord;
}

float get_shadow(vec2 coord, float refz) {
    #if GET_SETTING(PSSM, use_pcf)
        return texture(PSSMShadowAtlasPCF, vec3(coord, refz));
    #else
        float depth_sample = texture(PSSMShadowAtlas, coord, 0).x;
        return step(refz, depth_sample);
    #endif
}


void main() {

    #if HAVE_PLUGIN(Scattering)
        vec3 sun_vector = sun_azimuth_to_angle(
            TimeOfDay.Scattering.sun_azimuth,
            TimeOfDay.Scattering.sun_altitude);
        vec3 sun_color = TimeOfDay.Scattering.sun_color * 
            TimeOfDay.Scattering.sun_intensity * 10.0;
    #else
        vec3 sun_vector = normalize(pssm_sun_vector);
        vec3 sun_color = vec3(4.3, 4.25, 4.1) * 1.5;
    #endif




    // Get current scene color
    ivec2 coord = ivec2(gl_FragCoord.xy);
    vec4 scene_color = texelFetch(ShadedScene, coord, 0);


    if (sun_vector.z < 0.0) {
        result = scene_color;
        return;
    }

    // Get noise vector
    vec2 noise_vec = poisson_disk_2D_32[coord.x%4 + (coord.y%4)*4];

    // Get the material data
    Material m = unpack_material(GBuffer);

    // Variables to accumulate the shadows
    float shadow_factor = 0.0;
    vec3 lighting_result = vec3(0);

    // Find lowest split in range
    const int split_count = GET_SETTING(PSSM, split_count);
    int best_split = 999;
    float border_bias = 1.0 - (1.0 / 1.05);
    border_bias *= 0.5;

    for (int i = 0; i < split_count; ++i) {
        vec3 coord = project(pssm_mvps[i], m.position);
        if (coord.x >= border_bias && coord.x <= 1-border_bias && coord.y >= border_bias && coord.y <= 1-border_bias && coord.z >= 0.0 && coord.z <= 1.0) {
            best_split = i;
            break;
        }
    }

    int split = best_split;

    // Compute the shadowing factor
    // If we are out of the PSSM range:    
    if (split >= GET_SETTING(PSSM, split_count)) {

        // If we have the skybox, just stop
        if (is_skybox(m, cameraPosition)) {
            result = scene_color;
            return;

        // Otherwise assume no shadows
        } else {
            shadow_factor = 1.0;
        }

    } else {

        // Get the MVP for the current split        
        mat4 mvp = pssm_mvps[split];

        // Rotation is from 0 .. 1 whereas 0 means 0 degree and 1 means 90 degree
        // So 90 degree is half pi:
        float rotation = pssm_rotations[split] * HALF_PI;

        // Get the plugin settings
        const float slope_bias = GET_SETTING(PSSM, slope_bias) * 0.05;
        const float normal_bias = GET_SETTING(PSSM, normal_bias) * 0.005;
        const float fixed_bias = GET_SETTING(PSSM, fixed_bias) * 0.001;
        const int num_samples = GET_SETTING(PSSM, filter_sample_count);
        const float filter_radius = GET_SETTING(PSSM, filter_radius) / GET_SETTING(PSSM, resolution);


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
        vec2 filter_size = find_filter_size(mvp, sun_vector, filter_radius, rotation);


        #if GET_SETTING(PSSM, use_pcss)

            {
            /*
                
                PCSS Kernel

                Scan the region of the pixel for blockers, penumbra size is
                amount of blockers compared to non-blockers.

            */

            const int num_search_samples = GET_SETTING(PSSM, pcss_search_samples);

            float num_blockers = 0.0;
            float sum_blockers = 0.0;

            for (int i = 0; i < num_search_samples; ++i) {

                // Find random sample locations on a poisson disk
                vec2 offset = poisson_disk_2D_32[i];

                // Find depth at sample location
                float sampled_depth = texture(PSSMShadowAtlas,
                    projected_coord + offset * filter_size).x;

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
                ref_depth * GET_SETTING(PSSM, pcss_penumbra_size);

            // Apply penumbra size
            filter_size *= penumbra_size;

            }

        #endif


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

    }


    // Compute the sun lighting
    vec3 v = normalize(cameraPosition - m.position);
    vec3 l = sun_vector;
    lighting_result = applyLight(m, v, l, sun_color, 1.0, shadow_factor, vec4(0));


    // float factor = float(split) / GET_SETTING(PSSM, split_count);
    // lighting_result = (lighting_result+0.01) * vec3(factor, 1 - factor, 0);

    result = scene_color + vec4(lighting_result, 0);
}