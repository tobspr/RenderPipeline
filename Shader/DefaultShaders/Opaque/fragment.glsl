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

// This include enables us to compute the tangent in
// the fragment shader
#pragma include "Includes/TangentFromDDX.include"

uniform float osg_FrameTime;

void main() {

    // Create a material to store the properties on
    Material m = getDefaultMaterial();
    vec4 sampledDiffuse = texture(DIFFUSE_TEX, vOutput.texcoord);


    // sampledDiffuse.xyz = pow(sampledDiffuse.xyz, vec3(2.0)) * 1.1;
    
    // Alpha test
    // if (sampledDiffuse.a < 0.5) discard;

    vec4 sampledNormal  = texture(NORMAL_TEX, vOutput.texcoord);
    vec4 sampledSpecular = texture(SPECULAR_TEX, vOutput.texcoord);
    vec4 sampledRoughness = texture(ROUGHNESS_TEX, vOutput.texcoord);


    // sampledNormal = vec4(1);
    // sampledSpecular = vec4(1);
    // sampledRoughness = vec4(1);

    float bumpFactor = vOutput.materialDiffuse.w;
    float specularFactor = vOutput.materialSpecular.x;
    float metallic = vOutput.materialSpecular.y;
    float roughnessFactor = vOutput.materialSpecular.z;

    bumpFactor = 0.0;
   
    // sampledNormal.rgb = sampledDiffuse.rgb;

    vec3 detailNormal = sampledNormal.rgb * 2.0 - 1.0;

    vec3 tangent; vec3 binormal;
    reconstructTanBin(tangent, binormal);

    vec3 mixedNormal = mergeNormal(detailNormal, bumpFactor, vOutput.normalWorld, tangent, binormal);

    m.baseColor = sampledDiffuse.rgb * vOutput.materialDiffuse.rgb;
    m.roughness = sampledRoughness.r * roughnessFactor;
    m.specular = sampledSpecular.r * specularFactor;
    m.metallic = metallic;
    m.normal = mixedNormal;
    m.position = vOutput.positionWorld;


    // m.baseColor = mix(m.baseColor, vec3(1), m.metallic);

    #if 0
    m.metallic = 1.0;
    m.specular = 0.9;
    // m.roughness = 0.001 + m.baseColor.r*0.8;
    m.roughness = 0.02;
    #endif

    // m.baseColor = vec3(vOutput.materialDiffuse);
    // m.baseColor *= vec3(0.2,0.6,1.0) * 5.0;

    // m.metallic = 1.0;
    // m.roughness = 0.05;
    // m.specular = 1.0;

    // m.roughness = max(0.3, m.roughness);
    // m.specular = 1.0;
    // m.roughness = 0.0;

    // m.baseColor *= vec3(8);
    // m.roughness = 0.1;
    // m.specular = 0.0;
    // m.specular *= 0.15;
    // m.metallic = 1.0;


    renderMaterial(m);
}