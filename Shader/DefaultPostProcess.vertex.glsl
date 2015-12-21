#version 400

in vec4 p3d_Vertex;
out vec2 texcoord;

void main() {
    gl_Position = vec4(p3d_Vertex.xz, 0, 1);
    texcoord = fma(p3d_Vertex.xz, vec2(0.5), vec2(0.5));
}
