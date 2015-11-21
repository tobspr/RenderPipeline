#version 430

#pragma include "Includes/Configuration.inc.glsl"

in vec2 texcoord;
uniform sampler2D ShadedScene;

out vec4 result;

void main() {
    vec3 scene_color = texture(ShadedScene, texcoord).xyz;
    #if !DEBUG_MODE
        scene_color = sqrt(scene_color); // Simple SRGB
    #endif
    result = vec4(scene_color, 1);
}

