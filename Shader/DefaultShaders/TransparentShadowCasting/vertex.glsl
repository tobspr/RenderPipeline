#version 400

in vec4 p3d_Vertex;
uniform mat4 p3d_ModelViewProjectionMatrix;
uniform mat4 trans_model_to_world;

out vec3 worldpos;

void main() {
    gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;   
    worldpos = (trans_model_to_world * p3d_Vertex).xyz;
}