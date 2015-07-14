#version 420

in vec4 p3d_Vertex;
uniform mat4 p3d_ModelViewProjectionMatrix;
uniform mat4 trans_model_to_world;


in vec2 p3d_MultiTexCoord0;

out vec4 worldPos;
out vec2 texcoord;

#pragma ENTRY_POINT SHADER_IN_OUT

void main() {
    worldPos = trans_model_to_world * p3d_Vertex;
    gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;   
    texcoord = p3d_MultiTexCoord0;

    #pragma ENTRY_POINT SHADER_END

}