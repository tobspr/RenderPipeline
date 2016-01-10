/**
 * 
 * RenderPipeline
 * 
 * Copyright (c) 2014-2015 tobspr <tobias.springer1@gmail.com>
 * 
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 * 
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 * THE SOFTWARE.
 *
 */

#pragma once

#pragma include "Includes/Configuration.inc.glsl"
#pragma include "Includes/ColorSpaces/ColorSpaces.inc.glsl"

/*

Tonemapping Operators, some are from:
http://filmicgames.com/archives/75

A good sample using them can be found here:
https://www.shadertoy.com/view/lslGzl

*/

#if HAVE_PLUGIN(ColorCorrection)
    float exposure_adjustment = TimeOfDay.ColorCorrection.exposure_scale;
#else
    // Use fixed exposure in case color correction is not enabled
    const float exposure_adjustment = 2.0;
#endif


// No tonemapping
vec3 tonemap_none(vec3 color) {
    color *= exposure_adjustment;
    return color;
}

// Linear tonemapping
vec3 tonemap_linear(vec3 color)
{
   color *= exposure_adjustment; 
   return rgb_to_srgb(color);
}

// Different versions of the reinhard tonemap operator
vec3 tonemap_reinhard(vec3 color)
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

        // Reinhard operator based on luminance, but white preserving
        float white = 5.0;
        float luminance = get_luminance(color);
        vec3 rgb = color * (1.0 + luminance / (white * white)) / (1.0 + luminance);

    #elif ENUM_V_ACTIVE(ColorCorrection, reinhard_version, luminosity)

        // Reinhard operator in the CIE-Yxy color space
        vec3 xyY = rgb_to_xyY(color);
        
        // This saturates too much?
        xyY.z = xyY.z / (1.0 + xyY.z);

        // White preserving approach, doesn't work out well, too
        // xyY.z = xyY.z * (1.0 + xyY.z * (white*white)) / (1.0 + xyY.z);
        vec3 rgb = xyY_to_rgb(xyY);

    #else
        #error Unkown reinhard operator version!
    #endif

    return rgb_to_srgb(rgb);
}


// Optimized version of the Haarm-Peter Duiker’s curve
vec3 tonemap_optimized(vec3 color)
{
    color *= exposure_adjustment;
    vec3 x = max(vec3(0.0), color - 0.004);
    return (x * (6.2 * x + 0.5)) / (x * (6.2 * x + 1.7) + 0.06);
}

// Exponential tonemapping
vec3 tonemap_exponential(vec3 color) {
    color *= exposure_adjustment;
    color = 1.0 - exp( -GET_SETTING(ColorCorrection, exponential_factor) * color);
    return rgb_to_srgb(color);
}

// Alternative exponential tonemapping 
vec3 tonemap_exponential_2(vec3 color) {
    color *= exposure_adjustment;
    color = exp( -1.0 / ( 2.72 * color + 0.15 ) );
    return rgb_to_srgb(color);
}


// Uncharted 2 tonemapping formula
// See: http://de.slideshare.net/ozlael/hable-john-uncharted2-hdr-lighting
vec3 uncharted_2_tonemap_formula(vec3 x)
{
    const float A     = GET_SETTING(ColorCorrection, uc2t_shoulder_strength);
    const float B     = GET_SETTING(ColorCorrection, uc2t_linear_strength);
    const float C     = GET_SETTING(ColorCorrection, uc2t_linear_angle);
    const float D     = GET_SETTING(ColorCorrection, uc2t_toe_strength); 
    const float E     = GET_SETTING(ColorCorrection, uc2t_toe_numerator);
    const float F     = GET_SETTING(ColorCorrection, uc2t_toe_denumerator);
    return ((x*(A*x+C*B)+D*E)/(x*(A*x+B)+D*F))-E/F;
}

// Uncharted 2 tonemap operator
vec3 tonemap_uncharted2(vec3 color)
{
    const float white_base = GET_SETTING(ColorCorrection, uc2t_reference_white);
    color *= exposure_adjustment;
    const float exposure_bias = 2.0;
    vec3 curr = uncharted_2_tonemap_formula(exposure_bias * color);
    vec3 white = uncharted_2_tonemap_formula(vec3(white_base));
    return rgb_to_srgb(curr / white);
}

// Tonemapping selector
vec3 do_tonemapping(vec3 color) {
    
    // Clamp extreme values of the color
    color = clamp(color, 0.0, 1000.0);

    // Select tonemapping operator
    #if ENUM_V_ACTIVE(ColorCorrection, tonemap_operator, none)
        color = tonemap_none(color);
    #elif ENUM_V_ACTIVE(ColorCorrection, tonemap_operator, srgb)
        color = tonemap_linear(color);
    #elif ENUM_V_ACTIVE(ColorCorrection, tonemap_operator, optimized)
        color = tonemap_optimized(color);
    #elif ENUM_V_ACTIVE(ColorCorrection, tonemap_operator, reinhard)
        color = tonemap_reinhard(color);
    #elif ENUM_V_ACTIVE(ColorCorrection, tonemap_operator, uncharted2)
        color = tonemap_uncharted2(color);
    #elif ENUM_V_ACTIVE(ColorCorrection, tonemap_operator, exponential)
        color = tonemap_exponential(color);
    #elif ENUM_V_ACTIVE(ColorCorrection, tonemap_operator, exponential2)
        color = tonemap_exponential_2(color);
    #else
        #error Unkown tonemapping operator!
    #endif

    return color;
}
