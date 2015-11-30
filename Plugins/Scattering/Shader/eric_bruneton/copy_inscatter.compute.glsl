#version 440


#pragma include "./eric_bruneton/scattering_common.glsl"


layout(local_size_x = 8, local_size_y = 8, local_size_z = 8) in;

uniform sampler3D deltaSRSampler;
uniform sampler3D deltaSMSampler;
uniform layout(rgba32f) image3D dest;


void main() {
    ivec2 coord = ivec2(gl_GlobalInvocationID.xy);
    int layer = int(gl_GlobalInvocationID.z);

    vec3 ray = texelFetch(deltaSRSampler, ivec3(coord, layer), 0).xyz;
    vec3 mie = texelFetch(deltaSRSampler, ivec3(coord, layer), 0).xyz;
    // imageStore(dest, ivec3(coord, layer), vec4(ray.xyz, mie.x));
    imageStore(dest, ivec3(coord, layer), vec4(ray.xyz, mie.x));
}
