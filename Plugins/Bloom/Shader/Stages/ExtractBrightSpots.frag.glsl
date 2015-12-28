#version 400

#pragma include "Includes/Configuration.inc.glsl"
#pragma include "Includes/ColorSpaces/ColorSpaces.inc.glsl"

uniform sampler2D ShadedScene;
out vec4 result;
in vec2 texcoord;

void main() {
    vec3 scene_color = textureLod(ShadedScene, texcoord, 0).xyz;
    float luma = get_luminance(scene_color);
    vec3 bloom_color = vec3(0);
    if (luma > GET_SETTING(Bloom, minimum_luminance)) {

        // do reinhard tonemapping to avoid too bright spots
        // bloom_color = scene_color * 1.0 / (1.0 + get_luminance(scene_color));
        bloom_color = scene_color;
        // bloom_color = scene_color * 0.026;
        // bloom_color = make_logarithmic(scene_color, 4.0);        
        bloom_color *= GET_SETTING(Bloom, bloom_strength);
    }   

    #if DEBUG_MODE
        bloom_color *= 0;
    #endif

    result = vec4(bloom_color, 1.0);
}
