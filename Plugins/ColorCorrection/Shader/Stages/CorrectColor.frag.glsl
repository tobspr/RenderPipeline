#version 400

#pragma include "Includes/Configuration.inc.glsl"
#pragma include "Includes/Tonemapping.inc.glsl"


in vec2 texcoord;
uniform sampler2D ShadedScene;

out vec4 result;

void main() {

    vec3 scene_color = textureLod(ShadedScene, texcoord, 0).xyz;


    // Select tonemapping operator

    // Include the appropriate kernel
    #if ENUM_V_ACTIVE(ColorCorrection, tonemap_operator, none)
        scene_color = Tonemap_None(scene_color);
    #elif ENUM_V_ACTIVE(ColorCorrection, tonemap_operator, srgb)
        scene_color = Tonemap_Linear(scene_color);
    #elif ENUM_V_ACTIVE(ColorCorrection, tonemap_operator, optimized)
        scene_color = Tonemap_Optimized(scene_color);
    #elif ENUM_V_ACTIVE(ColorCorrection, tonemap_operator, reinhard)
        scene_color = Tonemap_Reinhard(scene_color);
    #elif ENUM_V_ACTIVE(ColorCorrection, tonemap_operator, uncharted2)
        scene_color = Tonemap_Uncharted2(scene_color);
    #elif ENUM_V_ACTIVE(ColorCorrection, tonemap_operator, exponential)
        scene_color = Tonemap_Exponential(scene_color);
    #else
        #error Unkown tonemapping operator
    #endif

    scene_color = saturate(scene_color);

    // Vignette
    scene_color *= 1.0 - smoothstep(0, 1, (length( (texcoord - vec2(0.5, 0.5)) * vec2(1.3, 1.0) * 1.1  ) - 0.2) ) * GET_SETTING(ColorCorrection, vignette_strength);




    result = vec4(scene_color, 1);
}