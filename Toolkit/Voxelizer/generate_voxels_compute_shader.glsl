#version 430

layout (local_size_x = 16, local_size_y = 16) in;


uniform writeonly image2D destination;
uniform sampler2DArray backfaceTex;
uniform sampler2DArray frontfaceTex;

uniform int gridSize;

vec2 getSolid(ivec3 coord) {
    if (any(lessThan(coord, ivec3(0))) ||
        any(greaterThan(coord, ivec3(gridSize-1))) ) {
        return vec2(0.6);
    }

    vec4 resultBackface = texelFetch(backfaceTex, ivec3(coord), 0);
    vec4 resultFrontface = texelFetch(frontfaceTex, ivec3(coord), 0);
    return vec2(resultFrontface.y, resultBackface.y);
}

void main() {
    ivec2 texelCoords = ivec2(gl_GlobalInvocationID.xy);
    float stencil = 0.0;

    for (int i = 0; i < gridSize; i++) {
        vec2 solidness = getSolid(ivec3(texelCoords, i));
        
        if (solidness.y > 0.5) {
            stencil = 1.0;
        }

        if (solidness.x > 0.5) {
            stencil = 0.0;
        }

        // imageStore(destination, texelCoords + ivec2(i*gridSize, 0), vec4(solidness,stencil,1));
        imageStore(destination, texelCoords + ivec2(i*gridSize, 0), vec4(stencil, stencil, stencil,1));
    }

    // now do the same from the other direction .. we don't know if the mesh has correct
    // walls
    stencil = 0.0;

    for (int i = gridSize-1; i >= 0; i--) {
        vec2 solidness = getSolid(ivec3(texelCoords, i));
        
        if (solidness.x > 0.5) {
            stencil = 1.0;
        }

        if (solidness.y > 0.5) {
            stencil = 0.0;
        }

        if (stencil > 0.5) {
            imageStore(destination, texelCoords + ivec2(i*gridSize, 0), vec4(stencil, stencil, stencil,1));
        }
    }


}