#pragma once

#pragma include "Includes/Configuration.inc.glsl"
#pragma include "Includes/Structures/Material.struct.glsl"
#pragma include "Includes/BRDF.inc.glsl"
#pragma include "Includes/IESLighting.inc.glsl"

// Computes the quadratic attenuation curve
float attenuation_curve(float dist, float radius) {
    #if 0
        return step(dist, radius);
    #endif

    #if 1
    float lin_att = 1.0 - saturate(dist / radius);
    float d_by_r = dist / radius + 1;
    return lin_att / max(0.001, d_by_r * d_by_r);
    #endif

    #if 0
    // As described in:
    // http://blog.selfshadow.com/publications/s2013-shading-course/karis/s2013_pbs_epic_notes_v2.pdf
    // Page 12
    float att = saturate(1.0 - pow(dist / radius, 4.0));
    return (att * att) / (dist * dist + 1.0);

    #endif
}

// Computes the attenuation for a point light
float get_pointlight_attenuation(vec3 l, float radius, float dist, int ies_profile) {
    float attenuation = attenuation_curve(dist, radius);
    return attenuation * get_ies_factor(l, ies_profile);
} 

// Computes the attenuation for a spot light
float get_spotlight_attenuation(vec3 l, vec3 light_dir, float fov, float radius, float dist, int ies_profile) {
    float dist_attenuation = attenuation_curve(dist, radius);
    float cos_angle = dot(l, -light_dir);

    // Rescale angle to fit the full range. We only do this for spot lights,
    // for point lights we use the actual angle
    float linear_angle = (cos_angle - fov) / (1 - fov);
    float angle_att = attenuation_curve(1 - linear_angle, 1.0);
    float ies_factor = get_ies_factor(ies_profile, linear_angle, 0);
    return ies_factor * angle_att * dist_attenuation;
}


// Computes a lights influence
// @TODO: Make this method faster
vec3 apply_light(Material m, vec3 v, vec3 l, vec3 light_color, float attenuation, float shadow, vec4 directional_occlusion, vec3 transmittance) {


    // Debugging: Fast rendering path
    #if 0
        return max(0, dot(m.normal, l)) * light_color * attenuation * m.basecolor * shadow;
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
    float NxV = max(1e-5, dot(m.normal, v));
    float NxH = max(0, dot(m.normal, h));
    float VxH = clamp(dot(v, h), 1e-5, 1.0);
    float LxH = max(0, dot(l, h));

    // Diffuse contribution
    vec3 shading_result = brdf_diffuse(NxV, LxH, m.roughness) * m.basecolor * (1 - m.metallic);

    // Specular contribution
    vec3 specular_color = mix(vec3(0.08) * m.specular, m.basecolor, m.metallic);
    float distribution = brdf_distribution(NxH, m.roughness);
    float visibility = brdf_visibility(NxL, NxV, NxH, VxH, m.roughness);
    vec3 fresnel = brdf_schlick_fresnel(specular_color, 0.5, VxH);
    shading_result += (distribution * visibility / M_PI) * fresnel;

    // Special case for directional occlusion and bent normals
    #if IS_SCREEN_SPACE && HAVE_PLUGIN(AO)

        // Compute lighting for bent normal
        float occlusion_factor = saturate(dot(vec4(l, 1.0), directional_occlusion));
        occlusion_factor = pow(occlusion_factor, 3.0);
        shading_result *= occlusion_factor;
    
    #endif  

    return (shading_result * light_color) * (attenuation * shadow * NxL) * transmittance;
}
