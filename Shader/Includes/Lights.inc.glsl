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
    // attenuation = linearAttenuation;
    // return step(r, d);
    return attenuation;
} 

vec3 applyLight(Material m, vec3 v, vec3 l, vec3 lightColor, float attenuation, float shadow) {

    // return lightColor * attenuation * fsaturate(dot(m.normal, l));

    m.roughness = 0.2;
    m.metallic = 1.0;


    vec3 shadingResult = vec3(0);
        
    // Skip shadows
    if (shadow < 0.001) 
        return shadingResult;

    vec3 specularColor = mix(vec3(0), m.diffuse, m.metallic);
    specularColor = m.diffuse;
    vec3 diffuseColor = mix(m.diffuse, vec3(0), m.metallic);

    vec3 n = m.normal;
    vec3 h = normalize(l + v);

    // Precomputed dot products
    float NxL = max(0, dot(n, l));
    float LxH = max(0, dot(l, h));
    float NxV = max(1e-5, dot(n, v));
    float NxH = max(0, dot(n, h));
    float VxH = max(0, dot(v, h));

    // Diffuse contribution
    shadingResult += lambertianBRDF(diffuseColor, NxL) * lightColor;

    // Specular contribution
    // Generalized microfacet specular

    float distribution = Distribution(m.roughness, NxH);
    float visibility = GeometricVisibility(m.roughness, NxV, NxL, VxH);
    vec3 fresnel = Fresnel( specularColor, VxH );

    shadingResult += distribution * visibility * fresnel * NxL * lightColor * NxV;


    return shadingResult * attenuation * shadow;

}