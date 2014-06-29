#version 430
// #pragma optionNV (unroll all)

#define MAX_VISIBLE_LIGHTS 64
#define MAX_LIGHTS_PER_PATCH 64

// Uniforms
// uniform samplerCube fallbackCubemap;
uniform mat4 lightData[MAX_VISIBLE_LIGHTS]; 
// uniform float lightCount; 
// uniform vec3 cameraPosition;
// uniform mat4 p3d_ProjectionMatrix;
// uniform mat4 p3d_ModelViewMatrix;
// uniform mat4[MAX_VISIBLE_LIGHTS] lightMatrices;


// Includes
#include "Includes/Configuration.include"
// #include "Includes/Packing.include"
// #include "Includes/Material.include"
// #include "Includes/LightingModels.include"
// #include "Includes/IntersectionTests.include"
// #include "Includes/Lighting.include"
// #include "Includes/PositionReconstruction.include"
// #include "Includes/LightDataPacking.include"

// Shared variables
// shared int visibleLights[64];
// shared int lightsSoFar;

// Texture in and outputs
layout (rgba8)   writeonly uniform image2D destinationImage;
// layout (rgba16f) readonly uniform image2D target0Image;
// layout (rgba16f) readonly uniform image2D target1Image;
// layout (rgba16f) readonly uniform image2D target2Image;
// layout (rgba16f) readonly uniform image2D minMaxDepthImage;

// Compute shader layout
layout (local_size_x = 16, local_size_y = 16) in;


void main() {

    // Position in compute space
    ivec2 computePos = ivec2(gl_GlobalInvocationID.xy);

    // Set local variables
    lightsSoFar = 0;

    // Size of the real screen
    const ivec2 realScreenSize = ivec2(1600, 928);

    // Size of the compute buffer. This might be bigger, because it always
    // has to be a multiple of vec2(local_size_x, local_size_y) 
    // and will get cropped later.
    const vec2 computeScreenSize = vec2(1600, 928);

    // Size of a patch
    vec2 patchSize = vec2(LIGHTING_COMPUTE_PATCH_SIZE_X, LIGHTING_COMPUTE_PATCH_SIZE_Y); 
    int threadCount = LIGHTING_COMPUTE_PATCH_SIZE_X * LIGHTING_COMPUTE_PATCH_SIZE_Y;


    // Position in precomputed space
    ivec2 precomputePos = ivec2(gl_WorkGroupID.xy);

    // Position in screen space coordinates
    vec2  screenPos  = vec2(gl_GlobalInvocationID.xy) / computeScreenSize;

    // Transform uniforms
    int intLightCount = int(lightCount);

    // Border visualization
    float borderFactor = 0.0;
    if (gl_LocalInvocationID.x < 1 || gl_LocalInvocationID.y < 1) 
        borderFactor = 1.0;
    
    // Fetch data from targets
    vec4 target0Data = imageLoad(target0Image, computePos);
    vec4 target1Data = imageLoad(target1Image, computePos);
    vec4 target2Data = imageLoad(target2Image, computePos);

    // Fetch packed material data
    Material material = unpackMaterial(target0Data, target1Data, target2Data);

    // Fetch patch min / max pos from previous pass
    vec4 patchMinMaxDepth = imageLoad(minMaxDepthImage, precomputePos).rgba;

    float patchLinearMinDepth = unpackDepth(patchMinMaxDepth.xy) * ndcFar;
    float patchLinearMaxDepth = unpackDepth(patchMinMaxDepth.zw) * ndcFar;

    // float patchMinDepth    = getZFromLinearZ(patchLinearMinDepth);
    // float patchMaxDepth    = getZFromLinearZ(patchLinearMaxDepth);

    // vec3 patchMinPosition = calculateSurfacePos(patchMinDepth, screenPos);
    // vec3 patchMaxPosition = calculateSurfacePos(patchMaxDepth, screenPos);

    // Compute tile bounds
    vec2 tileScale = computeScreenSize * 0.5f / patchSize;
    vec2 tileBias = tileScale - gl_WorkGroupID.xy;

    // Don't have to type that every time
    mat4 projMat = p3d_ProjectionMatrix;
    mat4 viewMat = p3d_ModelViewMatrix;

    vec4 frustumRL = vec4(-projMat[0][0] * tileScale.x, 0.0f, tileBias.x, 0.0f);
    vec4 frustumTL = vec4(0.0f, -projMat[1][1] * tileScale.y, tileBias.y, 0.0f);
    const vec4 frustumOffset = vec4(0.0f, 0.0f, -1.0f, 0.0f);

    // Derive frustum planes
    vec4 frustumPlanes[4];
    frustumPlanes[0] = normalize(frustumOffset - frustumRL);
    frustumPlanes[1] = normalize(frustumOffset + frustumRL);
    frustumPlanes[2] = normalize(frustumOffset - frustumTL);
    frustumPlanes[3] = normalize(frustumOffset + frustumTL);

    // Perform light culling
    int passCount = (intLightCount + threadCount - 1) / threadCount;

    // Allocate variables
    float dist;
    bool inFrustum;
    vec3 lightPos;
    float lightRadius;
    float lightType;

    int localInvocation = int(gl_LocalInvocationIndex);

    // for (int passIndex = 0; passIndex < passCount; passIndex ++) {
    //     // uint passIndex = 0;
    //     int lightIndex =  passIndex * threadCount + localInvocation;

    //     if (lightIndex < intLightCount) {
        
    //         mat4 lightData = lightData[lightIndex];
    //         lightType = Light_getType(lightData);


    //         inFrustum = false;

    //         if (lightType == 1) {
    //             lightPos    = Light_getPos(lightData);
    //             lightRadius = Light_getRadius(lightData);
    //             dist        = distance(material.position, lightPos);
            
    //             // inFrustum = true;

    //             // Check if distance matches
    //             if (dist - lightRadius < patchLinearMaxDepth) {

    //                 vec4 posProj = viewMat * vec4(lightPos, 1.0);

    //                 // Exact frustum culling
    //                 if (sphereInFrustum(frustumPlanes, posProj, lightRadius)) {
    //                     inFrustum = true;
    //                 }
    //             }
    //         }

    //         // Add to light list
    //         // if (inFrustum && lightsSoFar < MAX_LIGHTS_PER_PATCH) {
    //         //     int addIndex = atomicAdd(lightsSoFar, 1);
    //         //     visibleLights[addIndex] = lightIndex;
    //         // }
    //     }
    // }

    // barrier();

    // Calculate lighting / shadows
    vec4 lightingResult = vec4(0);

    // Now compute lighting, as we know now which lights are active
    // for this patch
    int localLightCount = min(MAX_LIGHTS_PER_PATCH, lightsSoFar);


    // lightingResult += lightData[0][0];


    #endif

    vec4 lightingResult = vec4(0);

    for (int i = 0; i < 4096; i++) {

        // int lightIndex = visibleLights[i];
        // int lightIndex = i % 64;
        // mat4 currentData = lightData[lightIndex];

        // Light currentLight;

        // currentLight.type = Light_getType(currentData);
        // currentLight.color = Light_getColor(currentData);
        // currentLight.position = Light_getPos(currentData);

        // lightingResult += computeLighting(currentLight, material, currentData);
        lightingResult += lightData[i%64][0] * 0.01;
        // lightingResult += i * 0.01;
        // lightingResult += vec4(i % 64) / 16000.0;
    }


    vec4 result = vec4(lightingResult.xyz, 1.0);


    // float intensityFactor = float(localLightCount) / float(MAX_LIGHTS_PER_PATCH);

    // if (borderFactor> 0.0) {
        // result.xyz = vec3(localLightCount > 0 ? 1.0 : 0.0);
    // result.xyz += vec3(intensityFactor, 1.0 - intensityFactor, 0.0) * 0.3;
    // result.xyz = vec3(intensityFactor);
    // }    

    // result.xyz = vec3(material.roughness *0.5);

    result.xyz = clamp(result.xyz, 0, 1);
    // result.xyz += vec3(1,1,0) * borderFactor * 0.09;

    imageStore(destinationImage, computePos, vec4(result) );
}