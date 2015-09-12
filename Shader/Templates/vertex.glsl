#version 430

#pragma include "Includes/Configuration.include"
#pragma include "Includes/Structures/VertexOutput.struct"

in vec4 p3d_Vertex;
in vec3 p3d_Normal;
in vec2 p3d_MultiTexCoord0;

uniform mat4 p3d_ModelViewProjectionMatrix;
uniform mat4 trans_model_to_world;


out layout(location=0) VertexOutput vOutput;

void main() {
    vOutput.texcoord = p3d_MultiTexCoord0;
    vOutput.normal = p3d_Normal;
    vOutput.position = (trans_model_to_world * p3d_Vertex).xyz;
    gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
}