#version 430

#pragma include "Includes/Configuration.inc.glsl"
#pragma include "Includes/LightCulling.inc.glsl"

uniform sampler2DArray FlaggedCells;
uniform layout(r32i) iimageBuffer cellListBuffer;
uniform writeonly iimage2DArray cellListIndices;

void main() {
    ivec2 coord = ivec2(gl_FragCoord.xy);
    float sumFlags = 0.0;

    // Iterate over all slices
    for (int i = 0; i < LC_TILE_SLICES; i++) {

        // Check if the cell is flagged
        float flag = texelFetch(FlaggedCells, ivec3(coord, i), 0).x;
        if (flag > 0.5) {

            // Append the cell and mark it
            int flagIndex = imageAtomicAdd(cellListBuffer, 0, 1) + 1;
            int cellData = coord.x | coord.y << 10 | i << 20;
            imageStore(cellListBuffer, flagIndex, ivec4(cellData));
            imageStore(cellListIndices, ivec3(coord, i), ivec4(flagIndex));
            sumFlags += float(flagIndex * 0.001) + 0.001;
        }
    }
}