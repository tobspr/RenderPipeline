#version 410

#include "Includes/Configuration.include"
#include "Includes/VertexOutput.include"

// Matrices
uniform mat4 trans_model_to_world;

// Material properties
in vec4 p3d_Vertex;
in vec3 p3d_Normal;
in vec3 p3d_Tangent;

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

uniform mat4 p3d_ModelViewProjectionMatrix;

// We need this for the velocity
uniform mat4 lastMVP;

uniform mat3 p3d_NormalMatrix;


void main() {

    // Transform normal to world space
    // vOutput.normalWorld   = normalize(p3d_NormalMatrix * p3d_Normal ).xyz;
    vOutput.normalWorld   = normalize(trans_model_to_world * vec4(p3d_Normal, 0) ).xyz;
    vOutput.tangentWorld  = normalize(trans_model_to_world * vec4(p3d_Tangent, 0) ).xyz;
    vOutput.binormalWorld = cross(vOutput.tangentWorld, vOutput.normalWorld);

    // Transform position to world space
    vOutput.positionWorld = (trans_model_to_world * p3d_Vertex).xyz;

    // Pass texcoord to fragment shader
    vOutput.texcoord = p3d_MultiTexCoord0.xy;

    // Also pass diffuse to fragment shader
    vOutput.materialDiffuse = p3d_Material.diffuse;
    vOutput.materialSpecular = p3d_Material.specular;
    vOutput.materialAmbient = p3d_Material.ambient.z;

    // Compute velocity in vertex shader, but it's important
    // to move the w-divide to the fragment shader
    vOutput.lastProjectedPos = lastMVP * vec4(vOutput.positionWorld, 1) * vec4(1,1,1,2);

    // Transform vertex to window space
    // Only required when not using tesselation shaders
    gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
}

