#version 420

#pragma include "Includes/Configuration.include"
#pragma include "Includes/Structures/VertexOutput.struct"
#pragma include "Includes/Structures/PandaMaterial.struct"

uniform mat4 trans_model_to_world;

// Material properties
in vec4 p3d_Vertex;

// Texture-Coordinate
in vec2 p3d_MultiTexCoord0;

// Outputs
layout(location=0) out VertexOutput vOutput;

uniform PandaMaterial p3d_Material;
uniform vec4 p3d_ColorScale;

uniform mat4 currentMVP;

#pragma ENTRY_POINT SHADER_IN_OUT
#pragma ENTRY_POINT FUNCTIONS

void main() {

    // Transform position to world space
    vOutput.positionWorld = (trans_model_to_world * p3d_Vertex).xyz;

    // Pass texcoord to fragment shader
    vOutput.texcoord = p3d_MultiTexCoord0.xy;
    
    #pragma ENTRY_POINT WS_POSITION

    // Transform vertex to window space
    // Only required when not using tesselation shaders
    gl_Position = currentMVP * vec4(vOutput.positionWorld, 1);

    #pragma ENTRY_POINT VERTEX_PROJECTION
    #pragma ENTRY_POINT SHADER_END
}

