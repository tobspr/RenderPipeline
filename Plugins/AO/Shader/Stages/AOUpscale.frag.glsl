#version 420

#pragma optionNV (unroll all)

#define USE_MAIN_SCENE_DATA
#pragma include "Includes/Configuration.inc.glsl"
#pragma include "Includes/GBuffer.inc.glsl"

out vec4 result;

uniform sampler2D SourceTex;
uniform GBufferData GBuffer;

void main() {
    
    // Get sample coordinates
    ivec2 coord = ivec2(gl_FragCoord.xy);
    ivec2 bil_start_coord = get_bilateral_coord(coord);
    
    // Get current pixel data
    float mid_depth = get_gbuffer_depth(GBuffer, coord);
    vec3 mid_nrm = get_gbuffer_normal(GBuffer, coord);

    const float max_depth_diff = 0.0006;
    const float max_nrm_diff = 0.002;

    float weights = 0.0;
    vec4 accum = vec4(0);

    // Accumulate all samples
    for (int x = 0; x < 2; ++x) {
        for (int y = 0; y < 2; ++y) {
            ivec2 source_coord = bil_start_coord + ivec2(x, y);
            ivec2 screen_coord = 2 * source_coord;
            vec4 source_sample = texelFetch(SourceTex, source_coord, 0);

            // Check how much information those pixels share, and if it is
            // enough, use that sample
            float sample_depth = get_gbuffer_depth(GBuffer, screen_coord);
            vec3 sample_nrm = get_gbuffer_normal(GBuffer, screen_coord);
            float depth_diff = abs(sample_depth - mid_depth) / max_depth_diff;
            float nrm_diff = max(0, dot(sample_nrm, mid_nrm));
            float weight = 1.0 - saturate(depth_diff);
            weight *= pow(nrm_diff, 1.0 / max_nrm_diff);

            weight = max(0.1, weight);

            accum += source_sample * weight;
            weights += weight;
        
        }
    }

    accum /= max(0.01, weights);
    result = vec4(accum);
}