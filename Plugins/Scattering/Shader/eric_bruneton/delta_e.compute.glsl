#version 440

#pragma include "./eric_bruneton/scattering_common.glsl"

layout(local_size_x = 16, local_size_y = 16) in;


uniform writeonly image2D dest;


void main() {
    ivec2 coord = ivec2(gl_GlobalInvocationID.xy);
    float r, muS;
    getIrradianceRMuS(r, muS);
    imageStore(dest, coord, vec4(transmittance(r, muS) * max(muS, 0.0), SCAT_DEBUG_ALPHA));

}