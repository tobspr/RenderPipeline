#version 400

#include "Includes/VertexOutput.include"

// Input from the vertex shader
in VertexOutput vOutput;

// Texture Samplers
uniform sampler2D p3d_Texture0;
uniform sampler2D p3d_Texture1;
uniform sampler2D p3d_Texture2;
uniform sampler2D p3d_Texture3;

// This is required for the materials
#include "Includes/MaterialPacking.include"

void main() {



    // Create a material to store the properties on
    Material m;

    vec4 sampledDiffuse = texture(DIFFUSE_TEX, vOutput.texcoord);
    vec4 sampledNormal  = texture(NORMAL_TEX, vOutput.texcoord);
    vec4 sampledSpecular = texture(SPECULAR_TEX, vOutput.texcoord);
    vec4 sampledRoughness = texture(ROUGHNESS_TEX, vOutput.texcoord);

    float bumpFactor = vOutput.materialDiffuse.w;
    float specularFactor = vOutput.materialSpecular.x;
    float metallic = vOutput.materialSpecular.y;
    float roughnessFactor = vOutput.materialSpecular.z;

    vec3 decodedNormal = sampledNormal.rgb * 2.0 - 1.0;
    // vec3 mixedNormal = normalize(vOutput.normalWorld + decodedNormal * bumpFactor * vOutput.normalWorld);
    vec3 mixedNormal = normalize(vOutput.normalWorld + bumpFactor * vOutput.normalWorld);

    m.baseColor = sampledDiffuse.rgb * vOutput.materialDiffuse.rgb;

    m.roughness = sampledRoughness.r * roughnessFactor;
    m.specular = sampledSpecular.r * specularFactor;
    m.metallic = metallic;

    m.position = vOutput.positionWorld;
    m.normal = vOutput.binormalWorld;



    renderMaterial(m);
}