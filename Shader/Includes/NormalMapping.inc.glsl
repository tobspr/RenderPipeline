#pragma once

// Reconstructs the tangent with the deltas of 
// the position and texcoord
void reconstruct_tangent(out vec3 tangent, out vec3 binormal) {
    vec3 pos_dx = dFdx(vOutput.position);
    vec3 pos_dy = dFdy(vOutput.position);
    float tcoord_dx = dFdx(vOutput.texcoord.y);
    float tcoord_dy = dFdy(vOutput.texcoord.y);
 
    // Fix issues when the texture coordinate is wrong, this happens when
    // two adjacent vertices have the same texture coordinate, as the gradient
    // is 0 then. We just assume some hard-coded tangent and binormal then
    if (abs(tcoord_dx) < 0.00001 && abs(tcoord_dy) < 0.00001) {
        vec3 base = abs(vOutput.normal.z) < 0.999 ? vec3(0, 0, 1) : vec3(0, 1, 0); 
        tangent = normalize(cross(vOutput.normal, base));
    } else {
        tangent = normalize(pos_dx * tcoord_dy - pos_dy * tcoord_dx);
    }

    binormal = normalize(cross(tangent, vOutput.normal));
}


// Aplies a normal map with a given base normal and displace normal, weighted by
// the bump factor
vec3 apply_normal_map(vec3 base_normal, vec3 displace_normal, float bump_factor) {
    vec3 tangent, binormal;
    reconstruct_tangent(tangent, binormal);
    displace_normal = mix(vec3(0, 0, 1), normalize(displace_normal), saturate(bump_factor));
    return vec3(
        tangent * displace_normal.x +
        binormal * displace_normal.y +
        base_normal * displace_normal.z
    );
}
