#version 400

in vec2 texcoord;
out vec4 result;

uniform int slice;
uniform sampler3D p3d_Texture0;

void main() {
    ivec2 coord = ivec2(texcoord * textureSize(p3d_Texture0, 0).xy);
    result.xyz = texelFetch(p3d_Texture0, ivec3(coord, slice), 0).xyz;
    result.w = 1.0;
}