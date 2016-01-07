#version 400

#pragma include "Includes/Configuration.inc.glsl"

uniform sampler2D SourceTex;
out vec4 result;

vec4 unpack_ao(vec4 data) {
    return vec4(
        normalize(fma(data.xyz, vec3(2.0), vec3(-1.0))),
        data.w
    );
}

void main() {
    ivec2 coord = ivec2(gl_FragCoord.xy);
    const ivec3 half_size = ivec3(SCREEN_SIZE_INT / 2, 0);

    vec4 accum = vec4(0);
    accum += unpack_ao(texelFetch(SourceTex, coord + half_size.zz, 0));
    accum += unpack_ao(texelFetch(SourceTex, coord + half_size.xz, 0));
    accum += unpack_ao(texelFetch(SourceTex, coord + half_size.zy, 0));
    accum += unpack_ao(texelFetch(SourceTex, coord + half_size.xy, 0));
    accum /= 4.0;
    result = vec4(fma(normalize(accum.xyz), vec3(0.5), vec3(0.5)), accum.w);
}
