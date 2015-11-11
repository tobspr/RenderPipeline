#pragma once


vec3 project(mat4 mvp, vec3 pos) {
    vec4 projected = mvp * vec4(pos, 1);
    return fma(projected.xyz / projected.w, vec3(0.5), vec3(0.5));
}




vec4 find_filter_size(mat4 projection, vec3 light, float sample_radius, float rotation) {

    // Scale y component by the slope
    light = normalize(light);
    float slope = max(0.05, abs(light.z) );


    // Find an arbitrary tangent and bitangent to the given normal
    vec3 v0 = abs(light.z) < 0.99 ? vec3(0, 0, 1) : vec3(1, 0, 0);
    vec3 tangent = normalize(cross(v0, light));
    vec3 binormal = normalize(cross(light, tangent));

    // tangent = vec3(1, 0, 0);
    // binormal = vec3(0, 1, 0);
    
    // tangent = vec3(0, 0, 0);
    // binormal = vec3(1, 1, 1);
    
    // Project everything
    // TODO: We could actually only use the 3x3 part of the mat and save the
    // origin projection.
    vec2 proj_origin = project(projection, vec3(0)).xy;
    vec2 proj_tangent = (project(projection, tangent).xy - proj_origin);
    vec2 proj_binormal = (project(projection, binormal).xy - proj_origin);

    proj_tangent = rotate(proj_tangent, -rotation);
    proj_binormal = rotate(proj_binormal, -rotation);


    // return proj_binormal.xyxy * sample_radius;

    return vec4(
            proj_tangent,
            proj_binormal) * sample_radius;
    // vec3 proj_offset = project(projection, vec3(1, 1, 1));

    // Get the difference between the projected vectors
    // vec2 delta = abs(proj_offset - proj_origin).xy;

    // return vec2(delta.x, delta.y / slope) * sample_radius;
    // return vec2(delta) * sample_radius;
}




// http://the-witness.net/news/2013/09/shadow-mapping-summary-part-1/
// Returns the normal and light dependent bias
vec2 get_shadow_bias(vec3 n, vec3 l) {
    float cos_alpha = saturate(dot(n, l));
    float offset_scale_n = sqrt(1 - cos_alpha*cos_alpha); // sin(acos(L·N))
    float offset_scale_l = offset_scale_n / cos_alpha;    // tan(acos(L·N))
    return vec2(offset_scale_n, min(2, offset_scale_l));
}


vec3 get_biased_position(vec3 pos, float slope_bias, float normal_bias, vec3 normal, vec3 light) {
    vec2 offsets = get_shadow_bias(normal, light);
    pos += normal * offsets.x * normal_bias;
    pos += light * offsets.y * slope_bias;
    return pos;
}

