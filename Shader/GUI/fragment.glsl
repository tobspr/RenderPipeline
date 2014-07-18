#version 150 

in vec2 texcoord;
uniform sampler2D p3d_Texture0;

in vec4 color;

out vec4 result;

void main() {
    result = vec4(color);
}