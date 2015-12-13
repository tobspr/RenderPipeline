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

    // todo: make the bias a setting
    if (luma > 7.0) {
        // do reinhard tonemapping to avoid too bright spots
        bloom_color = scene_color / (1 + scene_color);
        bloom_color *= 6;
        // bloom_color = scene_color;
    }   

    result = vec4(bloom_color, 1.0);
}
