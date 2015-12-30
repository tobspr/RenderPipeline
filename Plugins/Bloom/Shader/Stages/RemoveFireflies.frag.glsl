#version 430

#pragma optionNV (unroll all)r
#pragma include "Includes/Configuration.inc.glsl"
#pragma include "Includes/GaussianWeights.inc.glsl"
#pragma include "Includes/ColorSpaces/ColorSpaces.inc.glsl"

uniform sampler2D SourceTex;
in vec2 texcoord;
out vec3 result;

// Karis average
float get_weight(vec3 color, float weight) {
    return weight / (1.0 + get_luminance(color));
}

uniform ivec2 direction;

void main() {

    #if GET_SETTING(Bloom, remove_fireflies)
        float weights = 0.0;
        vec3 accum = vec3(0);
        const int filter_size = 6;

        vec2 texel_offs = direction / SCREEN_SIZE;

        // Find all surrounding pixels and weight them
        for (int i = -filter_size; i <= filter_size; ++i) {
            vec3 color_sample = textureLod(SourceTex, texcoord + i * texel_offs, 0).xyz;
            float weight = get_weight(color_sample, gaussian_weights_7[abs(i)]);
            accum += color_sample * weight;
            weights += weight;
        }

        accum /= max(0.01, weights);
        result = accum;
    #else
        result = textureLod(SourceTex, texcoord, 0).xyz;
    #endif
}
