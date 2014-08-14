#version 430

layout (local_size_x = 8, local_size_y = 8, local_size_z = 8) in;

uniform writeonly image2D destination;
uniform sampler2D source;
uniform int gridSize;


ivec2 convertCoord(ivec3 coord) {
    return coord.xy + ivec2(coord.z * gridSize, 0);
}


void main() {
    ivec3 texelCoords = ivec3(gl_GlobalInvocationID.xyz);

    ivec2 sourceCoords = convertCoord(texelCoords);

    float resultTop = texelFetch(source, convertCoord(texelCoords + ivec3(0,0,1)), 0).x;
    float resultBottom = texelFetch(source, convertCoord(texelCoords + ivec3(0,0,-1)), 0).x;
    float resultLeft = texelFetch(source, convertCoord(texelCoords + ivec3(1,0,0)), 0).x;
    float resultRight = texelFetch(source, convertCoord(texelCoords + ivec3(-1,0,0)), 0).x;
    float resultFront = texelFetch(source, convertCoord(texelCoords + ivec3(0,1,0)), 0).x;
    float resultBack = texelFetch(source, convertCoord(texelCoords + ivec3(0,-1,0)), 0).x;

    float resultVoxel = texelFetch(source, sourceCoords, 0);
    float neighbourCount = resultTop + resultBottom + resultLeft + resultRight + resultFront + resultBack;

    if (neighbourCount < 2.5) {
        resultVoxel *= 0.0;
    }

    // vec3 normal;
    // normal.x = resultLeft - resultRight;
    // normal.y = resultFront - resultBack;
    // normal.z = resultTop - resultBottom + 0.01;
    // normal = normalize(-normal);

    imageStore(destination, sourceCoords, vec4( resultVoxel ));
}