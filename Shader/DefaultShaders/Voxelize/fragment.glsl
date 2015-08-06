#version 420


#pragma include "Includes/Structures/VertexOutput.struct"

// Input from the vertex shader
layout(location=0) in VertexOutput vOutput;

// Texture Samplers
uniform sampler2D p3d_Texture0;
uniform sampler2D p3d_Texture1;
uniform sampler2D p3d_Texture2;
uniform sampler2D p3d_Texture3;

// This is required for the materials
#pragma include "Includes/Material.include"
#pragma include "Includes/CommonFunctions.include"

#pragma ENTRY_POINT SHADER_IN_OUT


out vec4 result;

void main() {
    // Sample the diffuse color
    vec4 sampledDiffuse = texture(p3d_Texture0, vOutput.texcoord);
    
    // Binary alpha test
    #if defined(USE_ALPHA_TEST)
        if (sampledDiffuse.a < 0.5) discard;
    #endif

    // Sample the other maps
    vec4 sampledNormal  = texture(p3d_Texture1, vOutput.texcoord);
    vec4 sampledSpecular = texture(p3d_Texture2, vOutput.texcoord);
    vec4 sampledRoughness = texture(p3d_Texture3, vOutput.texcoord);    
    vec3 mixedNormal = vOutput.normalWorld.xyz;

    float specularFactor = vOutput.materialSpecular.x;
    float metallic = vOutput.materialSpecular.y;
    float roughnessFactor = vOutput.materialSpecular.z;

    // Create a material to store the material type dependent properties on it
    Material m = getDefaultMaterial();
    m.position = vOutput.positionWorld;

    // Store the properties
    m.baseColor = sampledDiffuse.rgb * vOutput.materialDiffuse.rgb;
    m.roughness = sampledRoughness.r * roughnessFactor;
    m.specular = sampledSpecular.r * specularFactor;
    m.metallic = metallic;
    m.normal = mixedNormal;

    #pragma ENTRY_POINT MATERIAL

    // Write the material to the G-Buffer
    // renderMaterial(m);
    result = vec4(0.2,0.6,1.0,1.0);

}