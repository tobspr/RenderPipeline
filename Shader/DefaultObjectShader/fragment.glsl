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


    decodedNormal = normalize(decodedNormal);
    vec3 normal = decodedNormal;
    vec3 tangent = vOutput.tangentWorld;
    vec3 binormal = vOutput.binormalWorld;
    mat3 tangentToWorld = mat3(tangent, binormal, normal);
    vec3 mixedNormal = normalize(vec3(0, 0, 1) * tangentToWorld);

    // decodedNormal = normalize(decodedNormal);

    // decodedNormal.z = sqrt(1.0 - dot(decodedNormal.xy, decodedNormal.xy));
    m.baseColor = sampledDiffuse.rgb * vOutput.materialDiffuse.rgb;

    m.roughness = sampledRoughness.r * roughnessFactor;
    m.specular = sampledSpecular.r * specularFactor;
    m.metallic = metallic;

    m.normal = mixedNormal;

    // m.normal.xy *= 0.0;
    // m.normal.z *= 0.1;

    m.specular = 0.5;
    m.roughness = 0.01;

    // vec3 bitangent = cross(vOutput.normalWorld, vOutput.tangentWorld);
    // m.normal = normalize(abs(vOutput.tangentWorld) );

    m.position = vOutput.positionWorld;
    renderMaterial(m);
}