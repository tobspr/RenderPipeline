#pragma once

#pragma include "Includes/Configuration.inc.glsl"
#pragma include "Includes/Structures/Material.struct.glsl"
#pragma include "Includes/BRDF.inc.glsl"
#pragma include "Includes/IESLighting.inc.glsl"



float get_pointlight_attenuation(float radius, float dist) {

    // return step(d, r);

    // https://imdoingitwrong.wordpress.com/2011/01/31/light-attenuation/
    // Inverse falloff
    float attenuation = 1.0 / (1.0 + 2*dist/radius + (dist*dist)/(radius*radius)); 


    // Cut light transition starting at 80% because the curve is exponential and never really gets 0
    // float cutoff = r * 0.7;
    // attenuation *= 1.0 - saturate((d / cutoff) - 1.0) * (0.7 / 0.3);

    float linear = 1.0 - saturate(dist / radius);

    return linear;

    return max(0.0, attenuation * linear);
} 

// @TODO: Make this method faster
vec3 applyLight(Material m, vec3 v, vec3 l, vec3 light_color, float attenuation, float shadow, vec4 directional_occlusion, int ies_profile) {


    // Debugging: Fast rendering path
    #if 0
        // return max(0, dot(m.normal, l)) * lightColor * attenuation * m.diffuse;
    #endif

    // Compute ies profile
    attenuation *= get_ies_factor(l, ies_profile);

    // TODO: Check if skipping on low attenuation is faster than just shading
    // without any effect. Would look like this: if(attenuation < epsilon) return vec3(0);

    // Skip shadows, shold be faster than evaluating the BRDF on most cards,
    // at least if the shadow distribution is coherent
    if (shadow < 0.001) 
        return vec3(0);

    vec3 h = normalize(l + v);

    // Precomputed dot products
    float NxL = max(0, dot(m.normal, l));
    float NxV = max(0, dot(m.normal, v)) + 1e-7;
    float NxH = max(0, dot(m.normal, h));

    // Diffuse contribution
    vec3 shading_result = NxL * m.diffuse / M_PI;

    // Specular contribution
    float distribution = BRDFDistribution_GGX(NxH, m.roughness);
    float visibility = BRDFVisibilitySmithGGX(NxL, NxV, m.roughness);
    float fresnel = saturate(pow(NxV, 5.0)); // Simplified schlick
    shading_result += (distribution * visibility * fresnel) * m.specular;

    // Special case for directional occlusion and bent normals
    #if IS_SCREEN_SPACE && HAVE_PLUGIN(AO)

        // Compute lighting for bent normal
        float occlusion_factor = saturate(dot(vec4(l, 1), directional_occlusion));
        occlusion_factor = pow(occlusion_factor, 3.0);
        shading_result *= occlusion_factor;
    
    #endif


    return (shading_result * light_color) * (attenuation * shadow);
}
