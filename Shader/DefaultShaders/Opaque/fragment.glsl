#version 400


#pragma include "Includes/VertexOutput.include"

#extension GL_ARB_separate_shader_objects : enable

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

uniform float osg_FrameTime;

void main() {

    // Create a material to store the properties on
    Material m = getDefaultMaterial();

    // Sample the diffuse color
    vec4 sampledDiffuse = texture(p3d_Texture0, vOutput.texcoord);
    
    // Alpha test
    if (sampledDiffuse.a < 0.5) discard;

    // Sample the other maps
    vec4 sampledNormal  = texture(p3d_Texture1, vOutput.texcoord);
    vec4 sampledSpecular = texture(p3d_Texture2, vOutput.texcoord);
    vec4 sampledRoughness = texture(p3d_Texture3, vOutput.texcoord);
        
    // Extract the material properties 
    float bumpFactor = vOutput.materialDiffuse.w;
    float specularFactor = vOutput.materialSpecular.x;
    float metallic = vOutput.materialSpecular.y;
    float roughnessFactor = vOutput.materialSpecular.z;

    bumpFactor = 0.0;
    specularFactor = 0.5;
    metallic = 0.0;
    

    // sampledNormal.xyz = vec3(0.5, 0.5, 1.0);

    // Merge the detail normal with the vertex normal
    vec3 detailNormal = sampledNormal.xyz * 2.0 - 1.0;
    vec3 tangent; vec3 binormal;
    reconstructTanBin(tangent, binormal);
    vec3 mixedNormal = mergeNormal(detailNormal, bumpFactor, vOutput.normalWorld, tangent, binormal);

    // Store the properties
    m.baseColor = sampledDiffuse.rgb * vOutput.materialDiffuse.rgb;
    m.roughness = sampledRoughness.r * roughnessFactor;
    m.specular = sampledSpecular.r * specularFactor;
    m.metallic = metallic;
    m.normal = mixedNormal;
    m.position = vOutput.positionWorld;

    m.roughness = 0.7;


    // m.baseColor = vec3(sampledNormal.xyz);

    renderMaterial(m);
}