#version 440


#pragma include "common.glsl"


layout(local_size_x = 16, local_size_y = 16) in;


uniform float k;
uniform sampler2D deltaESampler;

uniform writeonly image2D dest;

void main() {
    ivec2 coord = ivec2(gl_GlobalInvocationID.xy);
    vec3 delta_e_val = texelFetch(deltaESampler, coord, 0).xyz;
    imageStore(dest, coord, vec4( vec3(k * delta_e_val), 1));
}