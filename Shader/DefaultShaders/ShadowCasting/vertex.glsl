#version 400

in vec4 p3d_Vertex;
in vec2 p3d_MultiTexCoord0;

uniform mat4 trans_model_to_world;
out vec2 vtxTexcoord;

uniform struct PandaMaterial {
    vec4 diffuse;
    vec3 specular;
    vec4 ambient;
} p3d_Material;

void main() {
    vtxTexcoord = p3d_MultiTexCoord0;
    gl_Position = trans_model_to_world * p3d_Vertex;   
}