#pragma once

#pragma include "Includes/Configuration.inc.glsl"
#pragma include "Includes/Structures/Material.struct.glsl"
#pragma include "Includes/BRDF.inc.glsl"
#pragma include "Includes/IESLighting.inc.glsl"


float get_pointlight_attenuation(vec3 l, float radius, float dist, int ies_profile) {

    // return step(d, r);

    // https://imdoingitwrong.wordpress.com/2011/01/31/light-attenuation/
    // Inverse falloff
    // float attenuation = 1.0 / (1.0 + 2*dist/radius + (dist*dist)/(radius*radius)); 

    float d_by_r = dist / radius + 1;
    float attenuation = 1 / (d_by_r * d_by_r);

    // Cut light transition starting at 80% because the curve is exponential and never really gets 0
    // float cutoff = r * 0.7;
    // attenuation *= 1.0 - saturate((d / cutoff) - 1.0) * (0.7 / 0.3);

    float linear = 1.0 - saturate(dist / radius);

    // return attenuation * linear;
    return max(0.0, attenuation * linear) * get_ies_factor(l, ies_profile);
} 


float get_spotlight_attenuation(vec3 l, vec3 light_dir, float fov, float radius, float dist, int ies_profile) {

    // float lin_attenuation = get_pointlight_attenuation(l, radius, dist, -1);
    float lin_attenuation = 1.0 - saturate(dist / radius);
    float angle = acos(dot(l, -light_dir));
    float angle_factor = 1 - saturate(angle / (0.5*fov) );

    angle_factor *= angle_factor;

    return lin_attenuation * get_ies_factor(ies_profile, 0.5*angle, 0);
}


// @TODO: Make this method faster
vec3 applyLight(Material m, vec3 v, vec3 l, vec3 light_color, float attenuation, float shadow, vec4 directional_occlusion) {


    // Debugging: Fast rendering path
    #if 0
        // return max(0, dot(m.normal, l)) * lightColor * attenuation * m.basecolor;
    #endif

    // TODO: Check if skipping on low attenuation is faster than just shading
    // without any effect. Would look like this: if(attenuation < epsilon) return vec3(0);

    // Skip shadows, shold be faster than evaluating the BRDF on most cards,
    // at least if the shadow distribution is coherent
    if (shadow < 0.001) 
        return vec3(0);

    vec3 h = normalize(l + v);

    // Precomputed dot products
    float NxL = max(0, dot(m.normal, l));
    float NxV = max(0, dot(m.normal, v)) + 1e-5;
    float NxH = max(0, dot(m.normal, h));
    float VxH = max(0, dot(v, h));
    float LxH = max(0, dot(l, h));

    // Diffuse contribution
    vec3 shading_result = brdf_diffuse(NxL, NxV, LxH, m.roughness) * 
        m.basecolor * (1 - m.metallic);

    // Specular contribution
    float distribution = brdf_distribution(NxH, m.roughness);
    float visibility = brdf_visibility(NxL, NxV, NxH, VxH, m.roughness);
    vec3 fresnel = brdf_fresnel(vec3(m.specular), VxH, NxV, LxH, m.roughness);
    shading_result += (distribution * visibility * fresnel) / M_PI; 

    // Special case for directional occlusion and bent normals
    #if IS_SCREEN_SPACE && HAVE_PLUGIN(AO)

        // Compute lighting for bent normal
        float occlusion_factor = saturate(dot(vec4(l, 1), directional_occlusion));
        occlusion_factor = pow(occlusion_factor, 3.0);
        shading_result *= occlusion_factor;
    
    #endif  


    return (shading_result * light_color) * (attenuation * shadow);
}
