#version 410


#pragma include "Includes/Structures/VertexOutput.struct"


// Input from the vertex shader
layout(location=0) in VertexOutput vOutput;

// Texture Samplers
uniform sampler2D p3d_Texture0;
uniform sampler2D p3d_Texture1;
uniform sampler2D p3d_Texture2;
uniform sampler2D p3d_Texture3;

// This is required for the materials
#pragma include "Includes/MaterialPacking.include"
#pragma include "Includes/CommonFunctions.include"

// This include enables us to compute the tangent in the fragment shader
#pragma include "Includes/TangentFromDDX.include"

void main() {

    // Create a material to store the properties on
    Material m = getDefaultMaterial();

    // Sample the diffuse color
    vec4 sampledDiffuse = texture(p3d_Texture0, vOutput.texcoord);
    
    // Alpha test
    // if (sampledDiffuse.a < 0.01) discard;

    // Sample the other maps
    vec4 sampledNormal  = texture(p3d_Texture1, vOutput.texcoord);
    vec4 sampledSpecular = texture(p3d_Texture2, vOutput.texcoord);
    vec4 sampledRoughness = texture(p3d_Texture3, vOutput.texcoord);
        
    // Extract the material properties 
    float bumpFactor = vOutput.materialDiffuse.w;
    bumpFactor = 0.0;


    // bumpFactor *= saturate(length(sampledNormal.w));

    float specularFactor = vOutput.materialSpecular.x;
    float metallic = vOutput.materialSpecular.y;
    float roughnessFactor = vOutput.materialSpecular.z;

    // Merge the detail normal with the vertex normal
    vec3 detailNormal = sampledNormal.xyz * 2.0 - 1.0;
    vec3 tangent; vec3 binormal;
    reconstructTanBin(tangent, binormal);

    // bumpFactor *= saturate(length(tangent));

    vec3 mixedNormal = mergeNormal(detailNormal, bumpFactor, vOutput.normalWorld, tangent, binormal);

    // Store the properties
    m.baseColor = sampledDiffuse.rgb * vOutput.materialDiffuse.rgb;
    m.roughness = sampledRoughness.r * roughnessFactor;
    m.specular = sampledSpecular.r * specularFactor;
    m.metallic = metallic;
    m.normal = mixedNormal;
    m.position = vOutput.positionWorld;


    // m.baseColor = sampledNormal.rgb; 
    m.roughness = 0.4;
    m.metallic = 0.0;
    m.specular = 1.0;
    // m.baseColor = vec3(sampledDiffuse.xyz);

    // m.baseColor = vec3(bumpFactor);

    // Write the material to the G-Buffer
    renderMaterial(m);
}