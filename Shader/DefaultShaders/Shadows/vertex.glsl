#version 420

#pragma include "Includes/Configuration.include"
#pragma include "Includes/Structures/VertexOutput.struct"

in vec4 p3d_Vertex;
uniform mat4 p3d_ViewProjectionMatrix;
uniform mat4 trans_model_to_world;


in vec2 p3d_MultiTexCoord0;

layout(location=0) out ShadowVertexOutput vOutput;

#pragma ENTRY_POINT SHADER_IN_OUT

#pragma ENTRY_POINT FUNCTIONS

void main() {
    vOutput.positionWorld = (trans_model_to_world * p3d_Vertex).xyz;
    vOutput.texcoord = p3d_MultiTexCoord0;

    #pragma ENTRY_POINT WS_POSITION

    gl_Position = p3d_ViewProjectionMatrix * vec4(vOutput.positionWorld, 1);

    #pragma ENTRY_POINT VERTEX_PROJECTION
    #pragma ENTRY_POINT SHADER_END

}