#version 430

#pragma include "Includes/Configuration.inc.glsl"
#pragma include "Includes/ColorSpaces/ColorSpaces.inc.glsl"

uniform sampler2D SourceTex;
uniform writeonly image2D DestTex;
in vec2 texcoord;

void main() {
    vec3 scene_color = textureLod(SourceTex, texcoord, 0).xyz;
    float luma = get_luminance(scene_color);
    vec3 bloom_color = vec3(0);
    if (luma > GET_SETTING(Bloom, minimum_luminance) * 2.0) {

        // do reinhard tonemapping to avoid too bright spots
        // bloom_color = scene_color * 1.0 / (1.0 + get_luminance(scene_color));
        bloom_color = scene_color;
        // bloom_color = scene_color * 0.026;
        // bloom_color = make_logarithmic(scene_color, 4.0);        
        bloom_color *= GET_SETTING(Bloom, bloom_strength) * 0.1;
    }   

    #if DEBUG_MODE
        bloom_color *= 0;
    #endif

    imageStore(DestTex, ivec2(gl_FragCoord.xy), vec4(bloom_color, 0));
}
