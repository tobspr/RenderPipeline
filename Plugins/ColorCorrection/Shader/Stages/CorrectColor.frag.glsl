#version 400

#pragma include "Includes/Configuration.inc.glsl"
#pragma include "Includes/Tonemapping.inc.glsl"
#pragma include "Includes/PositionReconstruction.inc.glsl"


in vec2 texcoord;
uniform sampler2D ShadedScene;
uniform vec3 cameraPosition;

out vec4 result;

void main() {

    vec3 scene_color = textureLod(ShadedScene, texcoord, 0).xyz;


    // Select tonemapping operator
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

    // Physically correct vignette, using the cos4 law:

    // Get the angle between the camera direction and the view direction
    vec3 material_dir = normalize(cameraPosition - calculateSurfacePos(1, texcoord));
    vec3 cam_dir = normalize(cameraPosition - calculateSurfacePos(1, vec2(0.5)));

    // According to the cos4 law, the brightness at angle alpha is cos^4(alpha).
    // Since dot() returns the cosine, we can just pow it to get a physically
    // correct vignette.    
    float cos_angle = dot(cam_dir, material_dir);
    float vignette = pow(cos_angle, 4.0);

    // Apply the vignette based on the vignette strength
    scene_color *= mix(1.0, vignette, GET_SETTING(ColorCorrection, vignette_strength));



    result = vec4(scene_color, 1);
}