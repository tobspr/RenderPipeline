#pragma once

#pragma include "Includes/Configuration.inc.glsl"


/*

BRDFs from:
http://www.frostbite.com/wp-content/uploads/2014/11/course_notes_moving_frostbite_to_pbr.pdf

*/


float ConvertRoughness(float roughness) {
    return saturate(pow(roughness, 3.0) + 0.003);
}


vec3 BRDFLambert(vec3 diffuse, float NxL) {
    return (diffuse * NxL) / M_PI;
}


vec3 BRDFSchlick(vec3 f0, float f90, float u)
{
    return f0 + ( f90 - f0 ) * pow(1.0 - u , 5.0);
}


float BRDFDistribution_Beckmann(float NxH, float roughness) {
    float nxh_sq = NxH * NxH;
    float rou_sq = roughness * roughness;

    float pot = (nxh_sq - 1) / (rou_sq * nxh_sq);
    return exp(pot) / (M_PI * rou_sq * nxh_sq * nxh_sq) / M_PI;
}


float BRDFDistribution_GGX(float NxH , float m)
{
    float m2 = m * m;
    float f = (NxH * m2 - NxH) * NxH + 1;
    return m2 / (f * f);
}

float BRDFGeometricVisibility_CookTorrance(float NxL, float NxV, float NxH, float VxH) {

    float nh_by_vh = (2.0 * NxH) / VxH;

    float eq_nv = NxV * nh_by_vh;
    float eq_nl = NxL * nh_by_vh;
    return min(1.0, min(eq_nv, eq_nl));
}


float BRDFDiffuseNormalized(float NxV, float NxL, float LxH, float roughness )
{
    float energyBias = mix(0.0, 0.5, roughness);
    float energyFactor = mix(1.0, 1.0 / 1.51, roughness);
    float fd90 = energyBias + 2.0 * LxH * LxH * roughness;
    vec3 f0 = vec3(1.0);
    float lightScatter = BRDFSchlick(f0, fd90, NxL).x;
    float viewScatter = BRDFSchlick(f0, fd90, NxV).x;
    return lightScatter * viewScatter * energyFactor;
}

float BRDFVisibilitySmithGGX(float NxL, float NxV, float roughness) {
    float rough_sq = roughness * roughness;
    float lambda_GGXV = NxL * sqrt((-NxV * rough_sq + NxV ) * NxV + rough_sq);
    float lambda_GGXL = NxV * sqrt((-NxL * rough_sq + NxV ) * NxL + rough_sq);
    return ( 0.5 / (lambda_GGXV + lambda_GGXL) ) * NxV * NxL * NxL;
}


float BRDFDistribution(float NxH, float roughness)
{
    NxH = max(0.0001, NxH);
    roughness = max(0.02, roughness);
    return BRDFDistribution_GGX(NxH, roughness);
}

