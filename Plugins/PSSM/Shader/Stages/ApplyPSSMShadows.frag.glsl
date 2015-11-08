#version 400

#pragma include "Includes/Configuration.inc.glsl"
#pragma include "Includes/PositionReconstruction.inc.glsl"
#pragma include "Includes/GBufferPacking.inc.glsl"
#pragma include "Includes/LightingPipeline.inc.glsl"
#pragma include "Includes/PoissonDisk.inc.glsl"
#pragma include "Includes/Shadows.inc.glsl"

out vec4 result;

// uniform vec3 cameraPosition;

uniform sampler2D GBufferDepth;
uniform sampler2D GBuffer0;
uniform sampler2D GBuffer1;
uniform sampler2D GBuffer2;
uniform sampler2D ShadedScene;

#if PSSM_USE_PCF
    uniform sampler2DShadow PSSMShadowAtlasPCF;
#endif

uniform sampler2D PSSMShadowAtlas;

uniform float pssm_split_distance;
uniform int pssm_split_count;
uniform mat4 pssm_mvps[PSSM_NUM_SPLITS];
uniform vec3 pssm_sun_vector;


vec2 get_split_coord(vec2 local_coord, int split_index) {
    local_coord.x = (local_coord.x + split_index) / float(pssm_split_count);
    return local_coord;
}

float get_shadow(vec2 coord, float refz) {
    #if PSSM_USE_PCF
        return texture(PSSMShadowAtlasPCF, vec3(coord, refz));
    #else
        float depth_sample = texture(PSSMShadowAtlas, coord, 0).x;
        return step(refz, depth_sample);
    #endif
}



void main() {

    // TODO: Move to python
    vec3 sun_vector = normalize(pssm_sun_vector);
    vec3 sun_color = vec3(4.5, 4.25, 4);

    // Get current scene color
    ivec2 coord = ivec2(gl_FragCoord.xy);
    vec4 scene_color = texelFetch(ShadedScene, coord, 0);

    // Get the material data
    Material m = unpack_material(GBufferDepth, GBuffer0, GBuffer1, GBuffer2);

    // Variables to accumulate the shadows
    float shadow_factor = 0.0;
    vec3 lighting_result = vec3(0);

    // Compute split index
    float depth = texelFetch(GBufferDepth, coord, 0).x;
    float linear_depth = getLinearZFromZ(depth);
    int split = int( log(1 + linear_depth / pssm_split_distance) * pssm_split_count);


    // Compute the shadowing factor
    // If we are out of the PSSM range:    
    if (split >= pssm_split_count) {

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

        // Get the dynamic and fixed bias
        const float slope_bias = 0.005;
        const float normal_bias = 0.005;
        const float fixed_bias = 0.0002;
        const int num_samples = 32;
        const int num_search_samples = 32;
        const float filter_radius = 35.0 / PSSM_RESOLUTION;
        
        vec3 biased_pos = get_biased_position(m.position, slope_bias, normal_bias, m.normal, sun_vector);

        // Project the current pixel to the view of the light
        vec3 projected = project(mvp, biased_pos);
        vec2 projected_coord = get_split_coord(projected.xy, split);

        // Do the actual filtering

        float ref_depth = projected.z - fixed_bias;

        // Find filter size
        vec2 filter_size = find_filter_size(mvp, sun_vector, filter_radius);

        // Find penumbra size

        float num_blockers = 0.0;
        float sum_blockers = 0.0;
        for (int i = 0; i < num_search_samples; ++i) {

            vec2 offset = poisson_disk_2D_32[i] * filter_size;
            float sampled_depth = texture(PSSMShadowAtlas, projected_coord + offset).x;
            float factor = step(sampled_depth, ref_depth);
            num_blockers += factor;
            sum_blockers += sampled_depth * factor;
        }

        float avg_blocker_depth = sum_blockers / num_blockers;
        float penumbra_size = abs(ref_depth - avg_blocker_depth) / ref_depth * 100.0;


        penumbra_size = max(0.001, penumbra_size);
        filter_size *= penumbra_size;

        // Do the actual filtering
        for (int i = 0; i < num_samples; ++i) {
            vec2 offset = poisson_disk_2D_32[i] * filter_size;
            shadow_factor += get_shadow(projected_coord + offset, ref_depth);
        }

        shadow_factor /= num_samples;

        shadow_factor *= 1.4;
        shadow_factor = saturate(shadow_factor);
    }

    // Compute the light influence
    vec3 v = normalize(cameraPosition - m.position);
    vec3 l = sun_vector;

    lighting_result = applyLight(m, v, l, sun_color, 1.0, shadow_factor);

    float split_f = split / float(pssm_split_count);
    // lighting_result *= rvec3(1 - split_f, split_f, 0);


    result = scene_color + vec4(lighting_result, 0);
}