#pragma once

#pragma include "Includes/Configuration.inc.glsl"
#pragma include "Includes/ColorSpaces.inc.glsl"

/*

Tonemapping Operators from:
http://filmicgames.com/archives/75

A good sample using them can be found here:
https://www.shadertoy.com/view/lslGzl

*/

#if HAVE_PLUGIN(ColorCorrection)
    float exposure_adjustment = TimeOfDay.ColorCorrection.exposure_scale;
#else
    const float exposure_adjustment = 2.0;
#endif




vec3 Tonemap_None(vec3 color) {
    color *= exposure_adjustment;
    return color;
}

vec3 Tonemap_Linear(vec3 color)
{
   color *= exposure_adjustment; 
   return rgb_to_srgb(color);
}

vec3 Tonemap_Reinhard(vec3 color)
{
    color *= exposure_adjustment;
    

    #if ENUM_V_ACTIVE(ColorCorrection, reinhard_version, rgb)

        // Simple reinhard operator in rgb space
        vec3 rgb = color / (1.0 + color);

    #elif ENUM_V_ACTIVE(ColorCorrection, reinhard_version, luminance)

        // Simple reinhard operator based on luminance
        float luminance = get_luminance(color);

        vec3 rgb = color / (1.0 + luminance);

    #elif ENUM_V_ACTIVE(ColorCorrection, reinhard_version, white_preserve)

        float white = 5.0;
        float luminance = get_luminance(color);

        vec3 rgb = color * (1.0 + luminance / (white * white)) / (1.0 + luminance);

    #elif ENUM_V_ACTIVE(ColorCorrection, reinhard_version, luminosity)

        vec3 xyY = rgb_to_xyY(color);
        
        // This doesn't work well, it saturates too much
        xyY.z = xyY.z / (1.0 + xyY.z);

        // Instead use a white preserving approach
        // xyY.z = xyY.z * (1.0 + xyY.z * (white*white)) / (1.0 + xyY.z);

        vec3 rgb = xyY_to_rgb(xyY);


    #else

        #error Unkown reinhard version!

    #endif


    return rgb_to_srgb(rgb);
}


vec3 Tonemap_Reinhard_Luminance(vec3 color) 
{
    color *= exposure_adjustment;

    // Reinhard operator in luminosity space

    float white = 0.3;
    vec3 xyY = rgb_to_xyY(color);
    
    // This doesn't work well, it saturates too much
    // xyY.z = xyY.z / (1.0 + xyY.z);

    // Instead use a white preserving approach
    xyY.z = xyY.z * (1.0 + xyY.z * (white*white)) / (1.0 + xyY.z);

    vec3 rgb = xyY_to_rgb(xyY);

    return rgb_to_srgb(rgb);
}

// Optimized version of the Haarm-Peter Duiker’s curve
vec3 Tonemap_Optimized(vec3 color)
{
    color *= exposure_adjustment;
    vec3 x = max(vec3(0.0), color - 0.004);
    return (x * (6.2 * x + 0.5)) / (x * (6.2 * x + 1.7) + 0.06);
}

vec3 Tonemap_Exponential(vec3 color) {
    color *= exposure_adjustment;
    // color = exp( -1.0 / ( 2.72 * color + 0.15 ) );
    color = 1.0 - exp( -GET_SETTING(ColorCorrection, exponential_factor) * color);
    return rgb_to_srgb(color);
}

// Uncharted 2 Tonemaping
const float UC2_A = 0.22;     // Shoulder Strength
const float UC2_B = 0.30;     // Linear Strength
const float UC2_C = 0.10;     // Linear Angle
const float UC2_D = 0.20;     // Toe Strength
const float UC2_E = 0.01;     // Toe Numerator
const float UC2_F = 0.30;     // Toe Denumerator
const float UC2_WHITE = 11.2; // Reference White


vec3 Uncharted2Tonemap(vec3 x)
{
   return ((x*(UC2_A*x+UC2_C*UC2_B)+UC2_D*UC2_E)/(x*(UC2_A*x+UC2_B)+UC2_D*UC2_F))-UC2_E/UC2_F;
}


vec3 Tonemap_Uncharted2(vec3 color)
{
    color *= exposure_adjustment;
    float exposure_bias = 2.0;
    vec3 curr = Uncharted2Tonemap(exposure_bias * color);
    vec3 white_scale = 1.0 / Uncharted2Tonemap(vec3(UC2_WHITE));
    vec3 final_color = curr * white_scale;
    return rgb_to_srgb(final_color);
}