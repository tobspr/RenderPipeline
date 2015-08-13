#version 400

uniform mat4 p3d_ModelViewProjectionMatrix;
in vec4 p3d_Vertex;
in vec2 p3d_MultiTexCoord0;
in vec4 p3d_Color;
uniform vec4 p3d_ColorScale;

out vec2 texcoord;
out vec4 colorMultiply;

void main() {
    gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
    texcoord = p3d_MultiTexCoord0;
    colorMultiply = p3d_ColorScale * p3d_Color;
}
