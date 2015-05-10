#version 410

#pragma include "Includes/Configuration.include"
#pragma include "Includes/VertexOutput.include"

// Matrices
uniform mat4 trans_model_to_world;
uniform mat4 tpose_world_to_model;

// Material properties
in vec4 p3d_Vertex;
in vec3 p3d_Normal;
in vec4 p3d_Color;

in vec2 p3d_MultiTexCoord0;


// Outputs
layout(location=0) out VertexOutput vOutput;

// We get the material info from panda as a struct
struct PandaMaterial {
    vec4 diffuse;
    vec3 specular;
    vec4 ambient;
};
uniform PandaMaterial p3d_Material;
uniform vec4 p3d_ColorScale;
uniform mat4 p3d_ModelViewProjectionMatrix;

// We need this for the velocity
uniform mat4 lastMVP;

void main() {

    // Transform normal to world space
    vOutput.normalWorld   = normalize(tpose_world_to_model * vec4(p3d_Normal, 0) ).xyz;

    // Transform position to world space
    vOutput.positionWorld = (trans_model_to_world * p3d_Vertex).xyz;
    // vOutput.positionWorld = (p3d_Vertex).xyz;

    // Pass texcoord to fragment shader
    // vOutput.texcoord = p3d_MultiTexCoord0.xy;
    vOutput.texcoord = p3d_MultiTexCoord0.xy;

    // Also pass diffuse to fragment shader
    vOutput.materialDiffuse = p3d_Material.diffuse * p3d_ColorScale * p3d_Color;
    vOutput.materialSpecular = p3d_Material.specular;
    vOutput.materialAmbient = p3d_Material.ambient.z;

    // Compute velocity in vertex shader, but it's important
    // to move the w-divide to the fragment shader
    vOutput.lastProjectedPos = lastMVP * vec4(vOutput.positionWorld, 1) * vec4(1,1,1,2);

    // Transform vertex to window space
    // Only required when not using tesselation shaders
    gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
}

