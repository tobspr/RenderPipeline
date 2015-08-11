#version 400

in vec2 texcoord;
in vec4 colorMultiply;
out vec4 color;


uniform sampler2D p3d_Texture0;

void main() {
    vec4 diffuse = texture(p3d_Texture0, texcoord);
    color = diffuse * colorMultiply;
}