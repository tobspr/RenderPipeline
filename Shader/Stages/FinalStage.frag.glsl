#version 430

#pragma include "Includes/Configuration.inc.glsl"

in vec2 texcoord;
uniform sampler2D ShadedScene;

out vec4 result;

void main() {

    vec4 sceneColor = texture(ShadedScene, texcoord);
    sceneColor = sqrt(sceneColor);

    // Vignette
   sceneColor *= 1.0 - smoothstep(0, 1, 
            (length( (texcoord - vec2(0.5, 0.5)) * vec2(1.3, 1.0) * 1.1  ) - 0.2) ) * 0.5;

    result.xyz = sceneColor.xyz;
    result.w = 1.0;
}

