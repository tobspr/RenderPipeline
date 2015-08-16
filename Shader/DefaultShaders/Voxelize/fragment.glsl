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
#pragma include "Includes/Material.include"
#pragma include "Includes/VoxelGeneration.include"
#pragma include "Includes/UBOs/Lights.ubo"
#pragma include "Includes/UBOs/Shadows.ubo"

#pragma ENTRY_POINT SHADER_IN_OUT
#pragma ENTRY_POINT FUNCTIONS

// Modify the lighting settings to get the lowest possible quality for voxelization

// Do not smooth cubemaps, that only works in the main scene pass
#undef CUBEMAP_ANTIALIASING_FACTOR
#define CUBEMAP_ANTIALIASING_FACTOR 0.0

// Don't use scattering attenuation
#define DISABLE_ATTENUATION_READ 1

// Don't use ies profiles
#define DISABLE_IES_PROFILES 1

// Don't use PBS
#define DISABLE_COMLPEX_LIGHTING 1

// Don't use Shadow filtering
#define DISABLE_PCSS 1
#define DISABLE_PCF 1

// Don't use diffuse AA
#define DISABLE_DIFFUSE_AA 1

// #define PSSM_FIXED_CASCADE_INDEX 4

// Lighting pass inputs
uniform isamplerBuffer renderedLightsBuffer;
uniform vec3 cameraPosition;

// #pragma include "Includes/Ambient.include"
// #pragma include "Includes/Lights.include"

// Lighting pipeline settings
#define PROCESS_SHADOWED_LIGHTS 1
#define PROCESS_UNSHADOWED_LIGHTS 1
#define IS_PER_TILE_LIGHTING 0

#pragma include "Includes/LightingPipeline.include"

out vec4 result;

void main() {
    // Sample the diffuse color
    vec4 sampledDiffuse = textureLod(p3d_Texture0, vOutput.texcoord, 0);
    
    // Binary alpha test
    #if defined(USE_ALPHA_TEST)
        if (sampledDiffuse.a < 0.5) discard;
    #endif

    // Sample the other maps
    // vec4 sampledNormal  = texture(p3d_Texture1, vOutput.texcoord);
    vec4 sampledSpecular = textureLod(p3d_Texture2, vOutput.texcoord, 0);
    vec4 sampledRoughness = textureLod(p3d_Texture3, vOutput.texcoord, 0);    

    float specularFactor = vOutput.materialSpecular.x;
    float metallic = vOutput.materialSpecular.y;
    float roughnessFactor = vOutput.materialSpecular.z;

    // sampledDiffuse.rgb = pow(sampledDiffuse.rgb, vec3(1.4));

    // Create a material to store the material type dependent properties on it
    Material m = getDefaultMaterial();
    m.position = vOutput.positionWorld;

    // Store the properties
    // m.baseColor = sampledDiffuse.rgb * vOutput.materialDiffuse.rgb;
    m.baseColor = vOutput.materialDiffuse.rgb;
    m.roughness = sampledRoughness.r * roughnessFactor;
    m.specular = sampledSpecular.r * specularFactor;
    m.metallic = metallic;
    m.normal = vOutput.normalWorld.xyz;

    // Make everything diffuse
    m.specular = 0.0;
    m.metallic = 0.0;
    m.roughness = 1.0;
    // m.baseColor = sampledDiffuse.rgb;
    // m.baseColor = vec3(1);

    #pragma ENTRY_POINT MATERIAL

    vec3 lightingResult = computeLighting(renderedLightsBuffer, m) * 0.2;
    result = vec4(lightingResult, 1);

    // lightingResult += vec3(1,1,1) * 0.2 * m.baseColor * GLOBAL_AMBIENT_FACTOR;

    // SRGB Correction

    // Dunno why, but this looks best
    lightingResult = pow(lightingResult, vec3(1.0 / 2.2));
    lightingResult = pow(lightingResult, vec3(1.0 / 2.2));
    lightingResult = pow(lightingResult, vec3(1.0 / 2.2));
    lightingResult = saturate(lightingResult);

    // Create a voxel for the material
    spawnVoxel(m.position, m.normal, lightingResult);
}