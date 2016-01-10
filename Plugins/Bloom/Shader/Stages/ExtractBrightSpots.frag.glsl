#version 430

#pragma include "Includes/Configuration.inc.glsl"
#pragma include "Includes/ColorSpaces/ColorSpaces.inc.glsl"

uniform sampler2D SourceTex;
uniform writeonly image2D RESTRICT DestTex;

void main() {
    ivec2 coord = ivec2(gl_FragCoord.xy);

    vec3 scene_color = texelFetch(SourceTex, coord, 0).xyz;
    float luma = get_luminance(scene_color);
    vec3 bloom_color = vec3(0);
    if (luma > GET_SETTING(Bloom, minimum_luminance) * 15.0) {
        bloom_color = scene_color;       
        bloom_color *= GET_SETTING(Bloom, bloom_strength) * 0.1;
    }   

    #if DEBUG_MODE
        bloom_color *= 0;
    #endif

    imageStore(DestTex, coord, vec4(bloom_color, 0));
}
