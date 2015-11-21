#pragma once

/*

Tonemapping Operators from:
http://filmicgames.com/archives/75

*/

const float exposure_adjustment = TimeOfDay.ColorCorrection.exposure_scale;

vec3 Tonemap_None(vec3 color) {
    color *= exposure_adjustment;
    return color;
}

vec3 Tonemap_Linear(vec3 color)
{
   color *= exposure_adjustment; 
   return pow(color, vec3(1/2.2));
}

vec3 Tonemap_Reinhard(vec3 color)
{
    color *= exposure_adjustment;
    color = color / (1 + color);
    return pow(color, vec3(1/2.2));
}

// Optimized version of the Haarm-Peter Duiker’s curve
vec3 Tonemap_Optimized(vec3 color)
{
    color *= exposure_adjustment;
    vec3 x = max(vec3(0.0), color - 0.004);
    return (x * (6.2 * x + 0.5)) / (x * (6.2 * x + 1.7) + 0.06);
}



// Uncharted 2 Tonemaping
const float TM_UC2_A = 0.15;
const float TM_UC2_B = 0.50;
const float TM_UC2_C = 0.10;
const float TM_UC2_D = 0.20;
const float TM_UC2_E = 0.02;
const float TM_UC2_F = 0.30;
const float TM_UC2_W = 11.2;

vec3 Uncharted2Tonemap(vec3 x)
{
   return ((x*(TM_UC2_A*x+TM_UC2_C*TM_UC2_B)+TM_UC2_D*TM_UC2_E)/(x*(TM_UC2_A*x+TM_UC2_B)+TM_UC2_D*TM_UC2_F))-TM_UC2_E/TM_UC2_F;
}


vec3 Tonemap_Uncharted2(vec3 color)
{
    color *= exposure_adjustment;
    float exposure_bias = 2.0;
    vec3 curr = Uncharted2Tonemap(exposure_bias * color);
    vec3 white_scale = 1.0 / Uncharted2Tonemap(vec3(TM_UC2_W));
    vec3 final_color = curr * white_scale;
    return pow(final_color, vec3(1.0 / 2.2));
}