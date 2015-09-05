#version 400

uniform mat4 p3d_ModelViewProjectionMatrix;

in vec4 p3d_Vertex;
out vec2 texcoord;

void main() {
    gl_Position = vec4(p3d_Vertex.x, p3d_Vertex.z, 0, 1);
    texcoord = sign(p3d_Vertex.xz * 0.5 + 0.5);
}