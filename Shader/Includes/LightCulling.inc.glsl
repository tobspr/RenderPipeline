#pragma once

#pragma include "Includes/Configuration.inc.glsl"
#pragma include "Includes/PositionReconstruction.inc.glsl"
#pragma include "Includes/Structures/Frustum.struct.glsl"


#define LIGHT_CULLING_DIST LC_MAX_DISTANCE
#define SLICE_POW_FACTOR 0.5


int getSliceFromLinearDepth(float linear_depth) {
    return int( 
        pow(linear_depth / LIGHT_CULLING_DIST, SLICE_POW_FACTOR) * LC_TILE_SLICES);
}

float getLinearDepthFromSlice(int slice) {
    return pow(slice / float(LC_TILE_SLICES), 1.0 / SLICE_POW_FACTOR) * LIGHT_CULLING_DIST;
}

ivec3 getCellIndex(ivec2 texcoord, float depth) {
    float linear_depth = getLinearZFromZ(depth);
    ivec2 tile = texcoord / ivec2(LC_TILE_SIZE_X, LC_TILE_SIZE_Y);
    return ivec3(tile, getSliceFromLinearDepth(linear_depth));
}


bool sphereInFrustum(Frustum frustum, vec4 pos, float radius) {
    bvec4 result;
    bvec2 result2;
    result.x = -radius <= dot(frustum.left, pos);
    result.y = -radius <= dot(frustum.right, pos);
    result.z = -radius <= dot(frustum.top, pos);
    result.w = -radius <= dot(frustum.bottom, pos);
    result2.x = -radius <= dot(frustum.nearPlane, pos);
    result2.y = -radius <= dot(frustum.farPlane, pos);
    return all(result) && all(result2);
}


bool isPointLightInFrustum(vec3 lightPos, float lightRadius, Frustum frustum) {
    vec4 projectedPos = frustum.viewMat * vec4(lightPos, 1);
    if (sphereInFrustum(frustum, projectedPos, lightRadius)) {
        return true;
    }
    return false;
}