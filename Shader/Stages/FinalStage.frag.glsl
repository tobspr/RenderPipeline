#version 430

#pragma include "Includes/Configuration.inc.glsl"
#pragma include "Includes/Tonemapping.inc.glsl"

in vec2 texcoord;
uniform sampler2D ShadedScene;

out vec4 result;

void main() {

    vec3 sceneColor = texture(ShadedScene, texcoord).xyz;


    #if !DEBUG_MODE
        // sceneColor = Tonemap_Linear(sceneColor);
        // sceneColor = Tonemap_Optimized(sceneColor);
        // sceneColor = Tonemap_Reinhard(sceneColor);
        sceneColor = Tonemap_Uncharted2(sceneColor);

        // Vignette
       // sceneColor *= 1.0 - smoothstep(0, 1, (length( (texcoord - vec2(0.5, 0.5)) * vec2(1.3, 1.0) * 1.1  ) - 0.2) ) * 0.5;


    #endif

    result.xyz = sceneColor;
    result.w = 1.0;
}

