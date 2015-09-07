#version 430

#pragma include  "Includes/Configuration.include"
#pragma include  "Includes/LightCulling.include"

out vec4 result;

uniform sampler2DArray FlaggedCells;
uniform layout(r32i) iimageBuffer cellListBuffer;
uniform writeonly iimage2DArray cellListIndices;

void main() {
    ivec2 coord = ivec2(gl_FragCoord.xy);
    result = vec4(1.0, 0.6, 0.2, 1.0);

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

    result = vec4(sumFlags / LC_TILE_SLICES);

    if (sumFlags < 0.00001) {
        result = vec4(0.3, 0, 0, 1);
    }

    result.w = 1.0;
}