#version 430

layout (local_size_x = 8, local_size_y = 8, local_size_z = 8) in;

uniform writeonly image2D destination;
uniform sampler2D source;
uniform int gridSize;
uniform float rejectionFactor;
uniform bool fillVolumes;
uniform bool discardInvalidVoxels;


ivec2 convertCoord(ivec3 coord) {
    return coord.xy + ivec2(coord.z * gridSize, 0);
}


void main() {
    ivec3 texelCoords = ivec3(gl_GlobalInvocationID.xyz);

    ivec2 sourceCoords = convertCoord(texelCoords);

    float resultTop = texelFetch(source, convertCoord(texelCoords + ivec3(0,0,1)), 0).w;
    float resultBottom = texelFetch(source, convertCoord(texelCoords + ivec3(0,0,-1)), 0).w;
    float resultLeft = texelFetch(source, convertCoord(texelCoords + ivec3(1,0,0)), 0).w;
    float resultRight = texelFetch(source, convertCoord(texelCoords + ivec3(-1,0,0)), 0).w;
    float resultFront = texelFetch(source, convertCoord(texelCoords + ivec3(0,1,0)), 0).w;
    float resultBack = texelFetch(source, convertCoord(texelCoords + ivec3(0,-1,0)), 0).w;

    vec4 resultVoxel = texelFetch(source, sourceCoords, 0);
    float neighbourCount = resultTop + resultBottom + resultLeft + resultRight + resultFront + resultBack;

    if (neighbourCount < rejectionFactor || (neighbourCount > 5.5 && !fillVolumes)) {
        resultVoxel *= 0.0;
    }

    if (discardInvalidVoxels && length(resultVoxel.xyz*4.0 - 2.0) < 0.01) {
        resultVoxel *= 0.0;
    }


    imageStore(destination, sourceCoords, vec4( resultVoxel.xyz * resultVoxel.w, resultVoxel.w ));
}