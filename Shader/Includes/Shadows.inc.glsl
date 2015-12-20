#pragma once

// Projects a point using the given mvp
vec3 project(mat4 mvp, vec3 p) {
    vec4 projected = mvp * vec4(p, 1);
    return fma(projected.xyz / projected.w, vec3(0.5), vec3(0.5));
}

// Given a shadow mvp matrix and the light vector, finds an appropriate filter size
vec2 find_filter_size(mat4 projection, vec3 light, float sample_radius) {

    // Scale y component by the slope
    // light = normalize(light);
    // float slope = max(0.05, abs(light.z) );

    // Get slope, since we have an up-vector of vec3(0, 0, 1), we can simply use
    // light.z
    // float slope = (max(0.05, abs(light.z)));

    // Find an arbitrary tangent and bitangent to the given normal
    vec3 tangent, binormal;
    tangent = vec3(1, 0, 0);
    binormal = vec3(0, 1, 0);
    // find_arbitrary_tangent(light, tangent, binormal);
    
    // Project everything
    // TODO: We could actually only use the 3x3 part of the mat and save the
    // origin projection.
    vec2 proj_origin = project(projection, vec3(0)).xy;
    vec2 proj_tangent = abs(project(projection, tangent + binormal).xy - proj_origin);
    // vec2 proj_binormal = (project(projection, binormal).xy - proj_origin);


    return vec2(proj_tangent * sample_radius) * 20.0;

}

// http://the-witness.net/news/2013/09/shadow-mapping-summary-part-1/
// Returns the normal and light dependent bias
vec2 get_shadow_bias(vec3 n, vec3 l) {
    float cos_alpha = saturate(dot(n, l));
    float offset_scale_n = sqrt(1 - cos_alpha*cos_alpha); // sin(acos(L·N))
    float offset_scale_l = offset_scale_n / cos_alpha;    // tan(acos(L·N))
    return vec2(offset_scale_n, min(2, offset_scale_l));
}

// Offsets a position based on slope and normal
vec3 get_biased_position(vec3 pos, float slope_bias, float normal_bias, vec3 normal, vec3 light) {
    vec2 offsets = get_shadow_bias(normal, light);
    pos += normal * offsets.x * normal_bias;
    pos += light * offsets.y * slope_bias;
    return pos;
}

