#version 420

#pragma include "Includes/Configuration.include"
#pragma include "Includes/Structures/VertexOutput.struct"
#pragma include "Includes/Structures/PandaMaterial.struct"

// Matrices
uniform mat4 trans_model_to_world;
uniform mat4 tpose_world_to_model;

// Material properties
in vec4 p3d_Vertex;
in vec3 p3d_Normal;
in vec4 p3d_Color;

// Texture-Coordinate
in vec2 p3d_MultiTexCoord0;

// Outputs
layout(location=0) out VertexOutput vOutput;

uniform PandaMaterial p3d_Material;
uniform vec4 p3d_ColorScale;

uniform mat4 trans_mainRender_to_clip_of_voxelizeCam;

#pragma ENTRY_POINT SHADER_IN_OUT
#pragma ENTRY_POINT FUNCTIONS

void main() {

    // Transform normal to world space
    vOutput.normalWorld = normalize(tpose_world_to_model * vec4(p3d_Normal, 0) ).xyz;

    // Transform position to world space
    vOutput.positionWorld = (trans_model_to_world * p3d_Vertex).xyz;

    // Pass texcoord to fragment shader
    vOutput.texcoord = p3d_MultiTexCoord0.xy;

    // Also pass diffuse to fragment shader
    vOutput.materialDiffuse = p3d_Material.diffuse * p3d_ColorScale * p3d_Color;
    vOutput.materialSpecular = p3d_Material.specular;
    vOutput.materialAmbient = p3d_Material.ambient.z;
    
    #pragma ENTRY_POINT WS_POSITION
    
    vOutput.lastProjectedPos = vec4(0);

    #pragma ENTRY_POINT SHADER_END

    // Transform vertex to window space
    gl_Position = trans_mainRender_to_clip_of_voxelizeCam * vec4(vOutput.positionWorld, 1);
   
    #pragma ENTRY_POINT VERTEX_PROJECTION
}

