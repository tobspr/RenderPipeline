#version 430

#pragma optionNV (unroll all)

#pragma include "Includes/Configuration.inc.glsl"
#pragma include "Includes/ColorSpaces/ColorSpaces.inc.glsl"

uniform sampler2D SourceTex;
out vec3 result;

// Karis average
float get_weight(vec3 color) {
    return 1.0 / (1.0 + get_luminance(color));
}

void main() {
    ivec2 coord = ivec2(gl_FragCoord.xy);

    #if GET_SETTING(Bloom, remove_fireflies)
        float weights = 0.0;
        vec3 accum = vec3(0);

        const int filter_size = 1;

        // Find all surrounding pixels and weight them
        for (int x = -filter_size; x <= filter_size; ++x) {
            for (int y = -filter_size; y <= filter_size; ++y) {
                vec3 color_sample = texelFetch(SourceTex, coord + ivec2(x, y), 0).xyz;
                float weight = get_weight(color_sample);
                accum += color_sample * weight;
                weights += weight;
            }
        }

        accum /= max(0.01, weights);
        result = accum;
    #else
        result = texelFetch(SourceTex, coord, 0).xyz;
    #endif
}
