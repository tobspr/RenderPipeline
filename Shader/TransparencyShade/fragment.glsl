#version 420


// #define UNSHADOWED_PASS 1

// Required, or it runs incredible slow
#pragma optionNV (unroll all)


#pragma include "Includes/Configuration.include"
#pragma include "Includes/TransparentMaterial.include"
#pragma include "Includes/PositionReconstruction.include"
#pragma include "Includes/Material.include"
#pragma include "Includes/UBOs/Lights.ubo"
#pragma include "Includes/UBOs/Shadows.ubo"


// Doesn't work with transparency
#undef CUBEMAP_ANTIALIASING_FACTOR
#define CUBEMAP_ANTIALIASING_FACTOR 0.0
#define DISABLE_ATTENUATION_READ 1


uniform isamplerBuffer renderedLightsBuffer;
uniform vec3 cameraPosition;

flat in uint batchOffset;
in vec2 texcoord;

uniform int frameIndex;

#if defined(USE_DEBUG_ATTACHMENTS)
out vec4 result;
#endif

layout(rgba32ui) uniform uimageBuffer materialDataBuffer;
uniform isampler2D pixelCountBuffer;

#pragma include "Includes/Ambient.include"
#pragma include "Includes/Lights.include"

// Lighting pipeline settings
#define PROCESS_SHADOWED_LIGHTS 1
#define PROCESS_UNSHADOWED_LIGHTS 1
#define IS_PER_TILE_LIGHTING 0

#pragma include "Includes/LightingPipeline.include"


void main() {

    // Extract total number of transparent pixels
    uint totalEntryCount = texelFetch(pixelCountBuffer, ivec2(0), 0).x;

    // Extract pixel id
    ivec2 pixelCoord = ivec2(gl_FragCoord.xy);
    uint pixelOffset = batchOffset + pixelCoord.x * TRANSPARENCY_BATCH_SIZE + pixelCoord.y;
    
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
    material.baseColor = tm.baseColor;
    material.position = calculateSurfacePos(tm.depth, tm.texcoord);
    material.normal = tm.normal; 
    material.roughness = tm.roughness;
    material.metallic = tm.metallic;
    material.specular = tm.specular;

    // Shade the pixel data
    vec3 lightingResult = computeLighting(renderedLightsBuffer, material);

    tm.baseColor = max(lightingResult * 0.5, vec3(0.0));


    // Compute ambient
    vec3 viewVector = normalize(cameraPosition - material.position);
    tm.baseColor += computeAmbient(material, vec4(1.0), vec4(0), 0.2, viewVector);
    // tm.baseColor *= 0.1;

    
    // Store the new pixel data
    uvec4 data1, data2;
    packTransparentMaterial(tm, data1, data2);
    imageStore(materialDataBuffer, int(pixelOffset)*2, data1);
    imageStore(materialDataBuffer, int(pixelOffset)*2+1, data2);

    #if defined(USE_DEBUG_ATTACHMENTS)
        result = vec4(tm.baseColor * 1.0, 1);
    #endif


}
