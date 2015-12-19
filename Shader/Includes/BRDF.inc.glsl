#pragma once

#pragma include "Includes/Configuration.inc.glsl"


/*

 BRDFs from:
 http://www.frostbite.com/wp-content/uploads/2014/11/course_notes_moving_frostbite_to_pbr.pdf

 Some also from:
 http://www.trentreed.net/blog/physically-based-shading-and-image-based-lighting/

*/


// Lambert BRDF 
float brdf_lambert(float NxL) {
    return NxL / M_PI;
}

// Proposed by Schlick 94
vec3 brdf_schlick_fresnel(vec3 f0, float f90, float u)
{
    // need to to a max(), produces artifacts otherwise for certain values
    return f0 + ( f90 - f0 ) * pow( max(0, 1.0 - u), 5.0);
}


// BRDF Proposed by Burley
float brdf_disney_diffuse(float NxV, float NxL, float LxH, float roughness) {

    // In case of squared roughness:
    float lin_roughness = sqrt(roughness);
    float energy_bias = mix(0.0, 0.5, lin_roughness);
    float energy_factor = mix(1.0, 1.0 / 1.51, lin_roughness);
    float fd90 = energy_bias + 2.0 * LxH * LxH * lin_roughness;
    vec3 f0 = vec3(1);
    float light_scatter = brdf_schlick_fresnel(f0, fd90, NxL).x;
    float view_scatter = brdf_schlick_fresnel(f0, fd90, NxV).x;
    return light_scatter * view_scatter * energy_factor * NxL / M_PI;
}

float brdf_distribution_blinn(float NxH, float roughness) {
    float r_sq = roughness * roughness;
    float n = 2.0 / r_sq - 2.0;
    return (n+2.0) / TWO_PI * pow(NxH, n);
}

float brdf_distribution_beckmann(float NxH, float roughness) {
    float r_cub = roughness * roughness;
    float NxH_sq = NxH * NxH;
    return exp( (NxH_sq - 1.0) / (r_cub * NxH_sq) ) / (M_PI * r_cub * NxH_sq * NxH_sq );
}

float brdf_distribution_ggx(float NxH , float roughness)
{
    float r_sq = roughness * roughness;
    float f = (NxH * r_sq - NxH) * NxH + 1;
    return r_sq / (f * f);
}

float brdf_visibility_implicit(float NxL, float NxV) {
    return NxL * NxV;
}

float brdf_visibility_neumann(float NxV, float NxL) {
    return NxL * NxV / max(0.1, 4.0 * max(NxL, NxV) );
}

float brdf_visibility_cook_torrance(float NxL, float NxV, float NxH, float VxH) {
    float nh_by_vh = 2.0 * NxH / VxH;
    float eq_nv = NxV * nh_by_vh;
    float eq_nl = NxL * nh_by_vh;
    return min(1.0, min(eq_nv, eq_nl));
}

float brdf_visibility_smith_ggx(float NxL, float NxV, float roughness) {
    float rough_sq = roughness * roughness;
    float lambda_GGXV = NxL * sqrt((-NxV * rough_sq + NxV ) * NxV + rough_sq);
    float lambda_GGXL = NxV * sqrt((-NxL * rough_sq + NxV ) * NxL + rough_sq);
    return ( 0.5 / (lambda_GGXV + lambda_GGXL) ) * NxV * NxL;
}


float brdf_visibility_schlick(float NxV, float NxL, float roughness) {
    float k = roughness * 0.5;
    float vis_schlick_v = NxV * (1.0 - k) + k;
    float vis_schlick_l = NxL * (1.0 - k) + k;
    return 0.25 / (vis_schlick_v * vis_schlick_l) * NxL * NxV;
}


vec3 brdf_fresnel_cook_torrance(vec3 specular, float VxH) {
    // TODO: FIXME
    vec3 sqrt_color = sqrt(clamp(specular, vec3(0), vec3(0.99)));
    vec3 n = (1.0 + sqrt_color) / (1.0 - sqrt_color);
    vec3 g = sqrt(n*n + VxH * VxH - 1.0);
    vec3 t1 = (g - VxH) / (g + VxH);
    vec3 t2 = ((g + VxH) * VxH - 1.0) / ((g - VxH) * VxH + 1.0);
    return 0.5 * t1 * t1 * (1 + t2 * t2);
}


// Diffuse BRDF
float brdf_diffuse(float NxL, float NxV, float LxH, float roughness) {
   
    // Choose one:
    // return brdf_lambert(NxL);
    return brdf_disney_diffuse(NxV, NxL, LxH, roughness);
}

// Distribution
float brdf_distribution(float NxH, float roughness)
{
    NxH = max(0.0001, NxH);
    
    // Choose one:
    // return brdf_distribution_blinn(NxH, roughness);
    // return brdf_distribution_beckmann(NxH, roughness);
    return brdf_distribution_ggx(NxH, roughness);
}

// Geometric Visibility
float brdf_visibility(float NxL, float NxV, float NxH, float VxH, float roughness) {
    
    // Choose one:
    // return brdf_visibility_neumann(NxV, NxL);
    // return brdf_visibility_schlick(NxV, NxL, roughness);
    // return brdf_visibility_cook_torrance(NxL, NxV, NxH, VxH);
    return brdf_visibility_smith_ggx(NxL, NxV, roughness);
}


// Fresnel
vec3 brdf_fresnel(vec3 specular, float VxH, float NxV, float LxH, float roughness) {
    float f90 = 0.5 + LxH * LxH * roughness;

    // Choose one:
    return brdf_schlick_fresnel(specular, f90, VxH);
    return brdf_fresnel_cook_torrance(specular, VxH);
}


