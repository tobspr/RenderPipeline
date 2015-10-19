#version 400

in vec2 texcoord;
out vec4 result;

uniform sampler2D p3d_Texture0;
uniform int mipmap;

void main() {
    ivec2 tcoord = ivec2(texcoord * textureSize(p3d_Texture0, mipmap).xy);
    result = texelFetch(p3d_Texture0, tcoord, mipmap);
    result.w = 1.0;
}