#version 420


#pragma include "Includes/Structures/VertexOutput.struct"


// Input from the vertex shader
layout(location=0) in VertexOutput vOutput;

// Texture Samplers
uniform sampler2D p3d_Texture0;
uniform sampler2D p3d_Texture1;
uniform sampler2D p3d_Texture2;
uniform sampler2D p3d_Texture3;

uniform int frameIndex;

// This is required for the materials
#pragma include "Includes/MaterialPacking.include"
#pragma include "Includes/CommonFunctions.include"

// This include enables us to compute the tangent in the fragment shader
#pragma include "Includes/TangentFromDDX.include"


#if defined(IS_TRANSPARENT)
    #pragma include "Includes/Transparency.include"
#endif

#pragma ENTRY_POINT SHADER_IN_OUT


void main() {

    // Sample the diffuse color
    vec4 sampledDiffuse = texture(p3d_Texture0, vOutput.texcoord);
    
    // Binary alpha test
    #if defined(USE_ALPHA_TEST)
        if (sampledDiffuse.a < 0.5) discard;
        
        // Testing
        // if (length(sampledDiffuse.sxyz) < 0.0001) discard;
    #endif

    // Sample the other maps
    vec4 sampledNormal  = texture(p3d_Texture1, vOutput.texcoord);
    vec4 sampledSpecular = texture(p3d_Texture2, vOutput.texcoord);
    vec4 sampledRoughness = texture(p3d_Texture3, vOutput.texcoord);
        


    // Extract the material properties
    #if defined(USE_NORMAL_MAPPING)
        float bumpFactor = vOutput.materialDiffuse.w;
        // bumpFactor *= 0.0;

        // Merge the detail normal with the vertex normal
        vec3 detailNormal = sampledNormal.xyz * 2.0 - 1.0;
        
        #pragma ENTRY_POINT DETAIL_NORMAL
        
        vec3 tangent; vec3 binormal;
        reconstructTanBin(tangent, binormal);
        vec3 mixedNormal = mergeNormal(detailNormal, bumpFactor, vOutput.normalWorld, tangent, binormal);
    #else
        vec3 mixedNormal = vOutput.normalWorld.xyz;
    #endif
    



    // Testing
    #if 0
        mixedNormal = vOutput.normalWorld.xzy * vec3(1,1,-1);
    #endif
        
    sampledDiffuse.xyz = pow(sampledDiffuse.xyz, vec3(1.7));

    float specularFactor = vOutput.materialSpecular.x;
    float metallic = vOutput.materialSpecular.y;
    float roughnessFactor = vOutput.materialSpecular.z;

    // Create a material to store the material type dependent properties on it
    #if defined(IS_TRANSPARENT)
        TransparentMaterial m = getDefaultTransparentMaterial();
        m.alpha = 0.5;
    #else
        Material m = getDefaultMaterial();
        m.position = vOutput.positionWorld;

        #if defined(USE_NORMAL_MAPPING)
            m.diffuseAAFactor = length(detailNormal);
        #endif

    #endif


    // Store the properties
    m.baseColor = sampledDiffuse.rgb * vOutput.materialDiffuse.rgb;
    m.roughness = sampledRoughness.r * roughnessFactor;
    m.specular = sampledSpecular.r * specularFactor;
    m.metallic = metallic;
    m.normal = mixedNormal;

    // m.baseColor = mix(vec3(1,0,0), sampledDiffuse.rgb, step(m.position.z, 0.001));
    // m.metallic = step(0.001, m.position.z);
    // m.roughness = 0.0;
    // m.specular = 1.0;

    m.baseColor = vec3(sampledDiffuse.rgb);


    #pragma ENTRY_POINT MATERIAL

    // Write the material to the G-Buffer
    #if defined(IS_TRANSPARENT)
        renderTransparentMaterial(m);
    #else
        renderMaterial(m);
    #endif
}