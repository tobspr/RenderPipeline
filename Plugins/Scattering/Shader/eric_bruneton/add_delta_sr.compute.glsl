#version 440



#pragma include "./eric_bruneton/scattering_common.glsl"


layout(local_size_x = 8, local_size_y = 8, local_size_z = 8) in;


uniform sampler3D deltaSSampler;
uniform layout(rgba32f) image3D dest;

void main() {

    ivec3 coord = ivec3(gl_GlobalInvocationID.xyz);

    float r;
    vec4 dhdH;
    get_r_dhdh(coord.z, r, dhdH);

    float mu, muS, nu;
    getMuMuSNu(r, dhdH, mu, muS, nu);

    vec4 orig_val = imageLoad(dest, coord);
    vec4 new_val = texelFetch(deltaSSampler, coord, 0) / phaseFunctionR(nu);
    imageStore(dest, coord, vec4(orig_val + new_val));

}