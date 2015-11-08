#pragma once


vec3 project(mat4 mvp, vec3 pos) {
    vec4 projected = mvp * vec4(pos, 1);
    return fma(projected.xyz / projected.w, vec3(0.5), vec3(0.5));
}


vec2 find_filter_size(mat4 projection, vec3 light, float sample_radius) {

    // Scale y component by the slope
    light = normalize(light);
    float slope = max(0.05, abs(light.z));

    // Find an arbitrary tangent and bitangent to the given normal
    vec3 v0 = abs(light.z) < 0.99 ? vec3(0, 0, 1) : vec3(1, 0, 0);
    vec3 tangent = normalize(cross(v0, light));
    vec3 binormal = normalize(cross(light, tangent));
    
    // Project 'em all
    vec3 proj_origin = project(projection, vec3(0));
    vec3 proj_offset = project(projection, tangent + binormal);

    // Get the difference between the projected vectors
    vec2 delta = abs(proj_offset - proj_origin).xy;
    float scale = (delta.x + (1.0 - slope) * delta.y) * sample_radius;

    return vec2(1, 1 / slope) * scale;
}


