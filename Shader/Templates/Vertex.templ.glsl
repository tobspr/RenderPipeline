#version 430

%DEFINES%

#pragma include "Includes/Configuration.inc.glsl"
#pragma include "Includes/Structures/VertexOutput.struct.glsl"

%INCLUDES%

in vec4 p3d_Vertex;
in vec3 p3d_Normal;
in vec2 p3d_MultiTexCoord0;

uniform mat4 p3d_ModelViewProjectionMatrix;
uniform mat4 trans_model_to_world;
uniform mat4 tpose_world_to_model;

%INOUT%

out layout(location=0) VertexOutput vOutput;

void main() {
    
    vOutput.texcoord = p3d_MultiTexCoord0;
    vOutput.normal = normalize(tpose_world_to_model * vec4(p3d_Normal, 0) ).xyz;
    vOutput.position = (trans_model_to_world * p3d_Vertex).xyz;
    
    %VERTEX%

    gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
    
    %TRANSFORMATION%

}