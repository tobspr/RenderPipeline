#pragma once

#pragma include "Includes/Configuration.inc.glsl"
#pragma include "Includes/Structures/Material.struct.glsl"
#pragma include "Includes/BRDF.inc.glsl"



float computePointLightAttenuation(float r, float d) {
    // https://imdoingitwrong.wordpress.com/2011/01/31/light-attenuation/
    // Inverse falloff
    float attenuation = 1.0 / (1.0 + 2*d/r + (d*d)/(r*r)); 

    // Cut light transition starting at 80% because the curve is exponential and never really gets 0
    // float cutoff = r * 0.7;
    // attenuation *= 1.0 - saturate((d / cutoff) - 1.0) * (0.7 / 0.3);

    float linearAttenuation = 1.0 - saturate(d / r);

    attenuation = max(0.0, attenuation * linearAttenuation);
    return attenuation;
} 

// @TODO: Make this method faster
vec3 applyLight(Material m, vec3 v, vec3 l, vec3 lightColor, float attenuation, float shadow, vec4 directional_occlusion) {

    // Debug: Fast rendering path
    // return max(0, dot(m.normal, l)) * lightColor * attenuation * m.diffuse;

    float scaled_roughness = ConvertRoughness(m.roughness);
    vec3 shadingResult = vec3(0);
        
    // Skip shadows
    if (shadow < 0.001) 
        return shadingResult;

    // vec3 specularColor = mix(vec3(0), m.diffuse, m.specular);
    vec3 specularColor = mix(vec3(1), m.diffuse * 2.0, m.metallic) * lightColor;
    vec3 diffuseColor = mix(m.diffuse, vec3(0), m.metallic);

    vec3 n = m.normal;
    vec3 h = normalize(l + v);

    // Precomputed dot products
    float NxL = max(0, dot(n, l));
    float LxH = max(0, dot(l, h));
    float NxV = abs(dot(n, v)) + 1e-7;
    float NxH = max(0, dot(n, h));
    float VxH = max(0, dot(v, h));

    // Diffuse contribution
    shadingResult = BRDFDiffuseNormalized(NxV, NxL, LxH, scaled_roughness) * NxL * lightColor * diffuseColor / M_PI;

    // Specular contribution
    float distribution = BRDFDistribution_GGX(NxH, scaled_roughness);
    float visibility = BRDFVisibilitySmithGGX(NxL, NxV, scaled_roughness);
    vec3 fresnel = BRDFSchlick( specularColor, VxH, scaled_roughness) * NxL * NxV / M_PI;

    // Energy conservation
    // float energy = 1.0 + pow(m.roughness * 1.0, 3.0);
    float energy = 1.0;

    shadingResult += (distribution * visibility * fresnel) / max(0.001, 4.0 * NxV * max(0.001, NxL) ) * energy * m.specular * specularColor;

    // Special case for DSSDO
    #if IS_SCREEN_SPACE && HAVE_PLUGIN(AO)
        float occlusion_factor = 1.0 - saturate(dot(vec4(-l, 0), directional_occlusion));
        occlusion_factor = pow(occlusion_factor, 3.0);
        shadingResult *= occlusion_factor;
    #endif

    // shadingResult *= 5.0;
    // attenuation = 1.0;

    return shadingResult * attenuation * shadow;
}