/**
 *
 * RenderPipeline
 *
 * Copyright (c) 2014-2016 tobspr <tobias.springer1@gmail.com>
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

#pragma include "render_pipeline_base.inc.glsl"
#pragma include "includes/material.struct.glsl"


/*

 BRDFs from:
 http://www.frostbite.com/wp-content/uploads/2014/11/course_notes_moving_frostbite_to_pbr.pdf

 Also from:
 http://www.trentreed.net/blog/physically-based-shading-and-image-based-lighting/

 Also inspired by the implementation in Disneys BRDF Explorer:
 http://www.disneyanimation.com/technology/brdf.html

*/


// Lambert BRDF
float brdf_lambert() {
    return ONE_BY_PI;
}

// Schlicks approximation to fresnel
vec3 brdf_schlick_fresnel(vec3 specular, float f90, float VxH)
{
    // Fast pow, proposed in
    // http://blog.selfshadow.com/publications/s2013-shading-course/karis/s2013_pbs_epic_notes_v2.pdf
    return mix(specular, vec3(f90), pow(2, (-5.55473*VxH-6.98316)*VxH));

    // Regular pow
    // return mix(specular, vec3(f90), pow( 1.0 - VxH, 5.0));
}

vec3 brdf_schlick_fresnel(vec3 specular, float VxH)
{
    return brdf_schlick_fresnel(specular, 1.0, VxH);
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



/* Distribution functions */
float brdf_distribution_blinn_phong(float NxH, float roughness) {
    float r_sq = roughness * roughness;
    float inv_r = 1.0 / r_sq;
    return inv_r * ONE_BY_PI * pow(NxH, fma(inv_r, 2.0, -2.0) );
}

float brdf_distribution_beckmann(float NxH, float roughness) {
    float r_sq = roughness * roughness;
    float nxh_sq = NxH * NxH;
    return exp( (nxh_sq - 1.0) / (r_sq * nxh_sq)) / (M_PI  * r_sq * nxh_sq * nxh_sq);
}

float brdf_distribution_ggx(float NxH , float roughness) {
    float nxh_sq = NxH * NxH;
    float tan_sq = (1 - nxh_sq) / nxh_sq;
    float f = roughness / max(1e-4, nxh_sq * (roughness * roughness + tan_sq) );
    return ONE_BY_PI * f * f;
}

float brdf_distribution_exponential(float NxH, float roughness) {
    float r_sq = roughness * roughness;
    float d = exp(-acos(NxH) / roughness); // TODO: optimize
    return d * (1.0 + 4.0 * r_sq) / (2.0 * r_sq * (1.0 + exp(-(M_PI/(2.0*roughness))))*M_PI);
}

float brdf_distribution_gaussian(float NxH, float roughness) {
    float theta = acos(NxH); // TODO: optimize
    return exp( -theta*theta / (roughness * roughness) );
}

float brdf_distribution_trowbridge_reitz(float NxH, float roughness) {
    float r_sq = roughness * roughness;
    float f = r_sq / (NxH * NxH * (r_sq - 1.0) + 1.0);
    return f * f * ONE_BY_PI / r_sq;
}


/* Visibility functions */
float brdf_visibility_implicit(float NxL, float NxV) {
    return NxL * NxV;
}

float brdf_visibility_neumann(float NxV, float NxL) {
    return NxL * NxV / max(1e-7, max(NxL, NxV));
}

float brdf_visibility_cook_torrance(float NxL, float NxV, float NxH, float VxH) {
    float nh_by_vh = 2.0 * NxH / VxH;
    float eq_nv = NxV * nh_by_vh;
    float eq_nl = NxL * nh_by_vh;
    return min(1.0, min(eq_nv, eq_nl));
}

float brdf_visibility_smith(float NxL, float NxV, float roughness) {
    float r_sq = roughness * roughness;
    float lambda_GGXV = NxL * sqrt((-NxV * r_sq + NxV ) * NxV + r_sq);
    float lambda_GGXL = NxV * sqrt((-NxL * r_sq + NxV ) * NxL + r_sq);
    return 1 / (lambda_GGXV + lambda_GGXL) * NxV * NxL;
}

// Helper function for the schlick visibility
float _schlick_g(float NxL, float roughness_sq) {
    float k = sqrt(2.0 * roughness_sq * ONE_BY_PI);
    return NxL > 0.0 ? NxL / (NxL - k * NxL + k) : 0.0;
}

float brdf_visibility_schlick(float NxV, float NxL, float roughness) {
    float r_sq = roughness * roughness;
    return _schlick_g(NxL, r_sq) * _schlick_g(NxV, r_sq);
}


/* Fresnel functions */

float ior_to_specular(float ior) {
    float f0 = (ior - 1) / (ior + 1);
    // Clamp between ior of 1 and 2.5
    return clamp(f0 * f0, 0.0, 0.18);
}

float brdf_fresnel_cook_torrance(float LxH, float roughness, float ior) {
    float g = sqrt(max(0, ior * ior + LxH * LxH - 1.0));
    float gpc = g + LxH;
    float gmc = g - LxH;
    return 0.5 * pow(gmc,2) / pow(gpc,2) * (1 + pow(LxH*(gpc)-1,2) / pow(LxH*(gmc)+1,2));
}

float brdf_fresnel_schlick_f0(float LxH, float roughness, float f0) {
    return f0 + (1 - f0) * pow(2, (-5.55473*LxH-6.98316)*LxH);
}

float brdf_fresnel_schlick(float LxH, float roughness, float ior) {
    float f0 = ior_to_specular(ior);
    return brdf_fresnel_schlick_f0(LxH, roughness, f0);
}

// Diffuse BRDF
float brdf_diffuse(float NxV, float LxH, float roughness) {

    // Choose one:
    return brdf_lambert();
    // return brdf_disney_diffuse(NxV, NxL, LxH, roughness);
}


// Distribution
float brdf_distribution(float NxH, float roughness)
{
    NxH = max(1e-6, NxH);

    // Choose one:
    // return brdf_distribution_blinn_phong(NxH, roughness);
    // return brdf_distribution_beckmann(NxH, roughness);
    // return brdf_distribution_exponential(NxH, roughness);
    // return brdf_distribution_gaussian(NxH, roughness);
    // return brdf_distribution_trowbridge_reitz(NxH, roughness);
    return brdf_distribution_ggx(NxH, roughness);
}

// Geometric Visibility
float brdf_visibility(float NxL, float NxV, float NxH, float VxH, float roughness) {

    // Choose one:
    float vis = brdf_visibility_neumann(NxV, NxL);
    // float vis = brdf_visibility_schlick(NxV, NxL, roughness);
    // float vis = brdf_visibility_cook_torrance(NxL, NxV, NxH, VxH);
    // float vis = brdf_visibility_smith(NxL, NxV, roughness);

    // Normalize the brdf
    return vis / max(1e-7, 4.0 * NxL * NxV);
}

// Fresnel
float brdf_fresnel(float LxH, float roughness) {
    // Default index of refraction
    // TODO: Maybe make this configurable?
    const float ior = 1.2;

    return brdf_fresnel_schlick(LxH, roughness, ior);
    // return brdf_fresnel_cook_torrance(LxH, roughness, ior);
}


/* Material Functions */
vec3 get_material_f0(Material m) {
    // Material specular is already in the 0 .. 0.08 range
    return mix(vec3(m.specular), m.basecolor, m.metallic);
}


// Returns a reflection vector, bent into the normal direction
vec3 get_reflection_vector(Material m, vec3 view_vector) {
    vec3 reflected_dir = reflect(view_vector, m.normal);
    // return reflected_dir;
    return mix(m.normal, reflected_dir,
        (1 - m.roughness) * (m.roughness + sqrt(1 - m.roughness)));
}


// Returns an approximated mipmap level based on the materials roughness
// level to approximate importance sampled references
float get_specular_mipmap(float roughness) {
    // Approximation to match importance sampled reference, tuned for a
    // resolution of 128.
    return max(0.01, roughness * 7.0 - pow(roughness, 6.0) * 1.5);
}

float get_specular_mipmap(Material m) {
    return get_specular_mipmap(m.roughness);
}
