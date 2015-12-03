#version 440



#pragma include "scattering_common.glsl"


layout(local_size_x = 16, local_size_y = 16) in;


uniform sampler2D deltaESampler;
uniform layout(rgba32f) image2D dest;

void main() {
    ivec2 coord = ivec2(gl_GlobalInvocationID.xy);
    vec3 delta_e_val = texelFetch(deltaESampler, coord, 0).xyz;
    vec4 irradiance_val = imageLoad(dest, coord);
    imageStore(dest, coord, vec4(delta_e_val + irradiance_val.xyz, irradiance_val.w));
}