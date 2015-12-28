#version 430

#pragma include "Includes/Configuration.inc.glsl"

uniform sampler2D ShadedScene;
uniform samplerBuffer Exposure;

out vec4 result;

void main() {
    ivec2 coord = ivec2(gl_FragCoord.xy);
    vec4 scene_color = texelFetch(ShadedScene, coord, 0);

    #if !DEBUG_MODE
        float avg_brightness = texelFetch(Exposure, 0).x;
        scene_color.xyz *= avg_brightness;
    #endif

    result = scene_color;
}
