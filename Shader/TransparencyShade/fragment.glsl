#version 420


// #define UNSHADOWED_PASS 1

// Required, or it runs incredible slow
#pragma optionNV (unroll all)


#pragma include "Includes/Configuration.include"
#pragma include "Includes/TransparentMaterial.include"
#pragma include "Includes/PositionReconstruction.include"
#pragma include "Includes/Material.include"
#pragma include "Includes/Structures/Light.struct"
#pragma include "Includes/Structures/ShadowSource.struct"

#pragma include "Includes/Ambient.include"



uniform Light lights[MAX_VISIBLE_LIGHTS]; 
uniform ShadowSource shadowSources[SHADOW_MAX_TOTAL_MAPS]; 

uniform isamplerBuffer renderedLightsBuffer;

uniform vec3 cameraPosition;

in vec2 texcoord;

out vec4 result;
flat in uint batchOffset;

layout(rgba32ui) uniform uimageBuffer materialDataBuffer;

uniform isampler2D pixelCountBuffer;

#pragma include "Includes/Lights.include"


void main() {

    // Extract total number of transparent pixels
    uint totalEntryCount = texelFetch(pixelCountBuffer, ivec2(0), 0).x;

    // Extract pixel id
    ivec2 pixelCoord = ivec2(gl_FragCoord.xy);
    uint pixelOffset = batchOffset + pixelCoord.x * 200 + pixelCoord.y;

    // Don't shade unused pixels
    if (pixelOffset > totalEntryCount) {
        discard;
    }

    // Extract pixel data
    uvec4 pixelData1 = imageLoad(materialDataBuffer, int(pixelOffset)*2);
    uvec4 pixelData2 = imageLoad(materialDataBuffer, int(pixelOffset)*2+1);
    TransparentMaterial tm = unpackTransparentMaterial(pixelData1, pixelData2);

    // Create a new materal, based on the shading model
    Material material = getDefaultMaterial();
    material.baseColor = tm.color;
    material.position = calculateSurfacePos(tm.depth, tm.texcoord);
    material.normal = tm.normal; 
    material.roughness = tm.roughness;
    material.metallic = tm.metallic;
    material.specular = tm.specular;

    // Shade the pixel data
    vec3 lightingResult = vec3(0);


    // Extract light counters
    // Init counters
    int processedPointLights = 0;
    int processedShadowedPointLights = 0;
    int processedDirectionalLights = 0;
    int processedShadowedDirectionalLights = 0;
    int processedSpotLights = 0;
    int processedShadowedSpotLights = 0;

    // Read light counts
    int countPointLight = min(MAX_POINT_LIGHTS, 
        texelFetch(renderedLightsBuffer, 0).r);

    int countPointLightShadow = min(MAX_SHADOWED_POINT_LIGHTS, 
        texelFetch(renderedLightsBuffer, 1).r);

    int countDirectionalLight = min(MAX_DIRECTIONAL_LIGHTS, 
        texelFetch(renderedLightsBuffer, 2).r);

    int countDirectionalLightShadow = min(MAX_SHADOWED_DIRECTIONAL_LIGHTS, 
        texelFetch(renderedLightsBuffer, 3).r);

    int countSpotLight = min(MAX_SPOT_LIGHTS, 
        texelFetch(renderedLightsBuffer, 4).r);

    int countSpotLightShadow = min(MAX_SHADOWED_SPOT_LIGHTS, 
        texelFetch(renderedLightsBuffer, 5).r);


    int currentBufferPos = 16;

    // Process Point Lights
    for (int i = 0; i < countPointLight; i++) {
        int index = texelFetch(renderedLightsBuffer, currentBufferPos + i).x;
        Light light = lights[index];
        lightingResult += applyPointLight(light, material, false);

    }

    currentBufferPos += MAX_POINT_LIGHTS;

    // Process shadowed point lights
    for (int i = 0; i < countPointLightShadow; i++) {
        int index = texelFetch(renderedLightsBuffer, currentBufferPos + i).x;
        Light light = lights[index];
        lightingResult += applyPointLight(light, material, true);
    }

    currentBufferPos += MAX_SHADOWED_POINT_LIGHTS;

    // Process directional lights
    for (int i = 0; i < countDirectionalLight; i++) {
        // No frustum check. Directional lights are always visible
        int index = texelFetch(renderedLightsBuffer, currentBufferPos + i).x;
        Light light = lights[index];
        lightingResult += applyDirectionalLight(light, material, false);
    }

    currentBufferPos += MAX_DIRECTIONAL_LIGHTS;

    // Process shadowed directional lights
    for (int i = 0; i < countDirectionalLightShadow; i++) {
        // No frustum check. Directional lights are always visible
        int index = texelFetch(renderedLightsBuffer, currentBufferPos + i).x;
        Light light = lights[index];
        lightingResult += applyDirectionalLight(light, material, true);

    }

    currentBufferPos += MAX_SHADOWED_DIRECTIONAL_LIGHTS;

    // Process Spot Lights
    for (int i = 0; i < countSpotLight; i++) {
        int index = texelFetch(renderedLightsBuffer, currentBufferPos + i).x;
        Light light = lights[index];
        lightingResult += applySpotLight(light, material, false);
    }

    currentBufferPos += MAX_SPOT_LIGHTS;


    // Process shadowed Spot lights
    for (int i = 0; i < countSpotLightShadow; i++) {
        int index = texelFetch(renderedLightsBuffer, currentBufferPos + i).x;
        Light light = lights[index];
        lightingResult += applySpotLight(light, material, true);
    }

    currentBufferPos += MAX_SHADOWED_SPOT_LIGHTS;

    tm.color = lightingResult * 0.1;


    // Compute ambient
    vec3 viewVector = normalize(cameraPosition - material.position);
    tm.color += computeAmbient(material, vec4(1), vec4(0), 1.0, viewVector) * 0.3;




    // Store the new pixel data
    uvec4 data1, data2;
    packTransparentMaterial(tm, data1, data2);
    imageStore(materialDataBuffer, int(pixelOffset)*2, data1);
    imageStore(materialDataBuffer, int(pixelOffset)*2+1, data2);

    result = vec4(tm.normal, 1);



}
