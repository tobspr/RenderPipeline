#version 430

#define USE_MAIN_SCENE_DATA
#pragma include "Includes/Configuration.inc.glsl"
#pragma include "Includes/LightCulling.inc.glsl"

uniform sampler2DArray FlaggedCells;
uniform layout(r32i) iimageBuffer cellListBuffer;
uniform writeonly iimage2DArray RESTRICT cellListIndices;

void main() {
    ivec2 coord = ivec2(gl_FragCoord.xy);

    // Iterate over all slices
    for (int i = 0; i < LC_TILE_SLICES; i++) {

        // Check if the cell is flagged
        bool visible = texelFetch(FlaggedCells, ivec3(coord, i), 0).x > 0.5;
        if (visible) {
            // Append the cell and mark it
            int flagIndex = imageAtomicAdd(cellListBuffer, 0, 1) + 1;
            int cellData = coord.x | coord.y << 10 | i << 20;
            imageStore(cellListBuffer, flagIndex, ivec4(cellData));
            imageStore(cellListIndices, ivec3(coord, i), ivec4(flagIndex));
        }
    }
}
