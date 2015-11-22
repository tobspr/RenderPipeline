#version 430

#pragma include "Includes/Configuration.inc.glsl"
#pragma include "Includes/PositionReconstruction.inc.glsl"
#pragma include "Includes/LightCulling.inc.glsl"
#pragma include "Includes/LightTypes.inc.glsl"
#pragma include "Includes/Structures/Frustum.struct.glsl"

out vec4 result;

uniform isamplerBuffer CellListBuffer;
uniform writeonly iimageBuffer perCellLightsBuffer;

uniform samplerBuffer AllLightsData;
uniform int maxLightIndex;

#define PROJ_MAT trans_view_of_mainCam_to_clip_of_mainCam
uniform mat4 PROJ_MAT;
uniform mat4 currentViewMatZup;

void main() {

    int sliceWidth = 512;
    ivec2 coord = ivec2(gl_FragCoord.xy);
    int idx = coord.x + coord.y * sliceWidth + 1;
    int numTotalCells = texelFetch(CellListBuffer, 0).x;

    if (idx > numTotalCells) {
        result = vec4(0.2, 0, 0, 1);
        return;
    }

    int packedCellData = texelFetch(CellListBuffer, idx).x;

    int cellX = packedCellData & 0x3FF;
    int cellY = (packedCellData >> 10) & 0x3FF;
    int cellSlice = (packedCellData >> 20) & 0x3FF;

    float linearDepthStart = getLinearDepthFromSlice(cellSlice);
    float linearDepthEnd = getLinearDepthFromSlice(cellSlice + 1);

    int storageOffs = (MAX_LIGHTS_PER_CELL+1) * idx;
    int numRenderedLights = 0;


    // Per tile bounds
    ivec2 precomputeSize = ivec2(LC_TILE_AMOUNT_X, LC_TILE_AMOUNT_Y);
    ivec2 patchSize = ivec2(LC_TILE_SIZE_X, LC_TILE_SIZE_Y);
    ivec2 virtualScreenSize = precomputeSize * patchSize;
    vec2 tileScale = vec2(virtualScreenSize) / vec2( 2.0 * patchSize);
    vec2 tileBias = tileScale - vec2(cellX, cellY);

    // Build frustum
    // Based on http://gamedev.stackexchange.com/questions/67431/deferred-tiled-shading-tile-frusta-calculation-in-opengl
    // (Which is based on DICE's presentation)
    vec4 frustumRL = vec4(-PROJ_MAT[0][0] * tileScale.x, 0.0f, tileBias.x, 0.0f);
    vec4 frustumTL = vec4(0.0f, -PROJ_MAT[2][1] * tileScale.y, tileBias.y, 0.0f);

    const vec4 frustumOffset = vec4(0.0f, 0.0f, -1.0f, 0.0f);

    // Calculate frustum planes
    Frustum frustum;
    frustum.left   = normalize(frustumOffset - frustumRL);
    frustum.right  = normalize(frustumOffset + frustumRL);
    frustum.top    = normalize(frustumOffset - frustumTL);
    frustum.bottom = normalize(frustumOffset + frustumTL);

    frustum.nearPlane = vec4(0, 0, -1.0, -linearDepthStart);
    frustum.farPlane = vec4(0, 0, 1.0, linearDepthEnd);
    frustum.viewMat = currentViewMatZup;

    // Cull all lights
    for (int i = 0; i < maxLightIndex + 1 && numRenderedLights < MAX_LIGHTS_PER_CELL; i++) {
        int dataOffs = i * 4;
        vec4 data0 = texelFetch(AllLightsData, dataOffs + 0);
        int lightType = int(data0.x);

        // No light
        if (lightType < 1) continue;

        vec4 data1 = texelFetch(AllLightsData, dataOffs + 1);
        vec4 data2 = texelFetch(AllLightsData, dataOffs + 2);
        vec4 data3 = texelFetch(AllLightsData, dataOffs + 3);

        bool visible = false;

        vec3 lightPos = data0.yzw;

        if (lightType == LT_POINT_LIGHT) {
            float radius = data1.w;
            visible = isPointLightInFrustum(lightPos, radius, frustum);
        }

        if (visible) {
            numRenderedLights ++;
            imageStore(perCellLightsBuffer, storageOffs + numRenderedLights, ivec4(i));
        }
    }

    imageStore(perCellLightsBuffer, storageOffs, ivec4(numRenderedLights));
    result = vec4(vec3(idx / 100.0 ), 1.0);
}