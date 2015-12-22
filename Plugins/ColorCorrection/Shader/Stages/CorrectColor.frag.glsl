#version 400

#pragma include "Includes/Configuration.inc.glsl"
#pragma include "Includes/Tonemapping.inc.glsl"
#pragma include "Includes/PositionReconstruction.inc.glsl"
#pragma include "Includes/Noise.inc.glsl"

#pragma include "../ChromaticAberration.inc.glsl"


in vec2 texcoord;
uniform sampler2D ShadedScene;
uniform samplerBuffer ExposureTex;
uniform sampler3D ColorLUT;
uniform vec3 cameraPosition;



out vec4 result;

uniform float osg_FrameTime;

vec3 apply_lut(vec3 color) {

    // Apply the Color LUT
    vec3 lut_coord = color;

    // We have a gradient from 0.5 / lut_size to 1 - 0.5 / lut_size
    // need to transform from 0 .. 1 to that gradient:
    float lut_start = 0.5 / 64.0;
    float lut_end = 1.0 - lut_start;
    lut_coord = (lut_coord + lut_start) * (lut_end - lut_start);
    return textureLod(ColorLUT, lut_coord, 0).xyz;
}

void main() {

    #if !DEBUG_MODE

        // Physically correct vignette, using the cos4 law:

        // Get the angle between the camera direction and the view direction
        vec3 material_dir = normalize(cameraPosition - calculate_surface_pos(1, texcoord));
        vec3 cam_dir = normalize(cameraPosition - calculate_surface_pos(1, vec2(0.5)));

        // According to the cos4 law, the brightness at angle alpha is cos^4(alpha).
        // Since dot() returns the cosine, we can just pow it to get a physically
        // correct vignette.    
        float cos_angle = dot(cam_dir, material_dir);
        float vignette = pow(cos_angle, 4.0);


        // Chromatic abberation
        #if GET_SETTING(ColorCorrection, use_chromatic_aberration)
            vec3 scene_color = do_chromatic_aberration(ShadedScene, texcoord, 1-vignette);
        #else
            vec3 scene_color = textureLod(ShadedScene, texcoord, 0).xyz;
        #endif

        // Automatic exposure
        #if GET_SETTING(ColorCorrection, use_auto_exposure)
            float avg_brightness = texelFetch(ExposureTex, 0).x;
            scene_color *= avg_brightness;
        #endif

        // Apply tonemapping
        scene_color = do_tonemapping(scene_color);

        // Compute film grain
        float film_grain = grain(texcoord, osg_FrameTime);
        vec3 blended_color = blend_soft_light(scene_color, vec3(film_grain));

        // Blend film grain
        float grain_factor = GET_SETTING(ColorCorrection, film_grain_strength);
        scene_color = mix(scene_color, blended_color, grain_factor);

        // Apply the LUT
        scene_color = apply_lut(scene_color);
        

        // Apply the vignette based on the vignette strength
        scene_color *= mix(1.0, vignette, GET_SETTING(ColorCorrection, vignette_strength));
    

    #else
        vec3 scene_color = textureLod(ShadedScene, texcoord, 0).xyz;
    #endif // !DEBUG_MODE

    scene_color = saturate(scene_color);

    result = vec4(scene_color, 1);
}