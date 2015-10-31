#version 400

in vec4 p3d_Vertex;
out vec2 texcoord;

void main() {
    gl_Position = vec4(p3d_Vertex.x, p3d_Vertex.y, 0, 1);
    texcoord = fma(p3d_Vertex.xy, vec2(0.5), vec2(0.5));
}
