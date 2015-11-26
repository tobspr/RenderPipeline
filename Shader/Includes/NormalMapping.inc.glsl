#pragma once



// Reconstructs the tangent with the deltas of 
// the position and texcoord
void reconstruct_tangent(out vec3 tangent, out vec3 binormal) {

    vec3 Q1 = dFdx(vOutput.position);
    vec3 Q2 = dFdy(vOutput.position);
    vec2 st1 = dFdx(vOutput.texcoord);
    vec2 st2 = dFdy(vOutput.texcoord);
 
    tangent = normalize(Q1*st2.y - Q2*st1.y);

    // Fix issues when the texture coordinate is wrong, this happens when
    // two adjacent vertices have the same texture coordinate, as the gradient
    // is 0 then. We just assume some hard-coded tangent and binormal then
    if (abs(st1.y) < 0.00001 && abs(st2.y) < 0.00001) {
        tangent = normalize(cross(vOutput.normal, vec3(0,1,0)));        
    }

    binormal = normalize(cross(tangent, vOutput.normal));

}


vec3 apply_normal_map(vec3 base_normal, vec3 displace_normal, float bump_factor) {
    vec3 tangent, binormal;
    reconstruct_tangent(tangent, binormal);

    displace_normal = normalize(displace_normal);
    displace_normal = mix(vec3(0, 0, 1), displace_normal, saturate(bump_factor));

    return (
        tangent * displace_normal.x +
        binormal * displace_normal.y +
        base_normal * displace_normal.z
    );
}
