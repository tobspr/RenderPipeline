#pragma once

#pragma include "Includes/Configuration.inc.glsl"
#pragma include "Includes/Structures/Material.struct.glsl"
#pragma include "Includes/BRDF.inc.glsl"
#pragma include "Includes/IESLighting.inc.glsl"

// Computes the quadratic attenuation curve
float attenuation_curve(float dist, float radius) {
    // return step(dist, radius);
    float lin_att = 1.0 - saturate(dist / radius);
    float d_by_r = dist / radius + 1;
    return lin_att / max(0.001, d_by_r * d_by_r) * TWO_PI;
}

// Computes the attenuation for a point light
float get_pointlight_attenuation(vec3 l, float radius, float dist, int ies_profile) {
    float attenuation = attenuation_curve(dist, radius);
    return attenuation * get_ies_factor(l, ies_profile);
} 

// Computes the attenuation for a spot light
float get_spotlight_attenuation(vec3 l, vec3 light_dir, float fov, float radius, float dist, int ies_profile) {
    float dist_attenuation = attenuation_curve(dist, radius);
    float angle = acos(-1e-6 + dot(l, -light_dir));
    float angle_factor = attenuation_curve(angle, fov);
    float ies_factor =  get_ies_factor(ies_profile, 0.5*angle, 0);
    return angle_factor * dist_attenuation * ies_factor;
}


// Computes a lights influence
// @TODO: Make this method faster
vec3 apply_light(Material m, vec3 v, vec3 l, vec3 light_color, float attenuation, float shadow, vec4 directional_occlusion, vec3 transmittance) {


    // Debugging: Fast rendering path
    #if 0
        return max(0, dot(m.normal, l)) * light_color * attenuation * m.basecolor;
    #endif

    // TODO: Check if skipping on low attenuation is faster than just shading
    // without any effect. Would look like this: if(attenuation < epsilon) return vec3(0);

    // Skip shadows, should be faster than evaluating the BRDF on most cards,
    // at least if the shadow distribution is coherent
    // HOWEVER: If we are using translucency, we have to also consider shadowed
    // areas. So for now, this is disabled. If we reenable it, we probably should
    // also check if translucency is greater than a given epsilon.
    // if (shadow < 0.001) 
        // return vec3(0);

    // Weight transmittance by the translucency factor
    transmittance = mix(vec3(1), transmittance, m.translucency);

    // Translucent objects don't recieve shadows, this just makes them look weird.
    shadow = mix(shadow, 1, saturate(m.translucency));

    // Compute the dot product, for translucent materials we also add a bias
    vec3 h = normalize(l + v);
    float NxL = saturate(10.0 * m.translucency + dot(m.normal, l));
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
    vec3 fresnel = brdf_fresnel(vec3(1), VxH, NxV, LxH, m.roughness);
    shading_result += (distribution * visibility * fresnel) / TWO_PI * m.specular; 

    // Special case for directional occlusion and bent normals
    #if IS_SCREEN_SPACE && HAVE_PLUGIN(AO)

        // Compute lighting for bent normal
        float occlusion_factor = saturate(dot(vec4(l, 1.0), directional_occlusion));
        occlusion_factor = pow(occlusion_factor, 3.0);
        shading_result *= occlusion_factor;
    
    #endif  
    return (shading_result * light_color) * (attenuation * shadow) * transmittance;
}
