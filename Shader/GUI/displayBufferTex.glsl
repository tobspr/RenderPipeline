#version 400

in vec2 texcoord;
out vec4 result;

uniform samplerBuffer p3d_Texture0;

void main() {
    int offs = int(texcoord.x * 100.0);
    result = texelFetch(p3d_Texture0, offs);
    result.w = 1.0;
}