#version 430

#pragma include "Includes/Configuration.inc.glsl"

uniform sampler2D ShadedScene;
out vec4 result;

void main() {

    vec2 texcoord = get_texcoord();
    
    // Fetch the current's scene color
    vec3 scene_color = textureLod(ShadedScene, texcoord, 0).xyz;
    
    #if !DEBUG_MODE
        // Do a simple sRGB correction
        scene_color = sqrt(scene_color);
    #endif
    
    result = vec4(scene_color, 1);
}

