#version 400

in vec4 p3d_Vertex;
out vec2 texcoord;

void main() {
    gl_Position = vec4(p3d_Vertex.x, p3d_Vertex.y, 0, 1);
    texcoord = p3d_Vertex.xy * 0.5 + 0.5;
}