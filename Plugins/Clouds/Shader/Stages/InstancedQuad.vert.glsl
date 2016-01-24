#version 400
in vec4 p3d_Vertex;
flat out int instance_id;

void main() {
    gl_Position = vec4(p3d_Vertex.xz, 0, 1);
    instance_id = gl_InstanceID;
}
