#version 430

#pragma include "Includes/Configuration.inc.glsl"

in vec2 texcoord;
uniform sampler2D ShadedScene;

out vec4 result;

void main() {

    vec4 sceneColor = texture(ShadedScene, texcoord);

    vec3 correctedColor = sceneColor.xyz;   
    correctedColor = pow(correctedColor * 1.4, vec3(1.0 / 2.2));
    
    result.xyz = correctedColor;
    result.w = 1.0;
}

