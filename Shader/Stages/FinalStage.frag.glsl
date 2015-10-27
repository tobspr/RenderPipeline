#version 430

#pragma include "Includes/Configuration.inc.glsl"

in vec2 texcoord;
uniform sampler2D ShadedScene;

out vec4 result;

void main() {

    vec4 sceneColor = texture(ShadedScene, texcoord);

    vec3 correctedColor = sceneColor.xyz;   
    correctedColor = pow(correctedColor, vec3(1.0 / 2.2));
    

    // Vignette
   correctedColor *= 1.0 - smoothstep(0, 1, 
            (length( (texcoord - vec2(0.5, 0.5)) * vec2(1.3, 1.0) * 1.1  ) - 0.2) ) * 0.5;

    result.xyz = correctedColor;
    result.w = 1.0;
}

