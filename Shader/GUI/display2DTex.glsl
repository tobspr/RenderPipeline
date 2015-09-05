#version 400

in vec2 texcoord;
out vec4 result;

uniform sampler2D p3d_Texture0;

void main() {
    ivec2 tcoord = ivec2(texcoord * textureSize(p3d_Texture0, 0).xy);
    result = texelFetch(p3d_Texture0, tcoord, 0);
    result.w = 1.0;
}