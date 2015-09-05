#version 430

#pragma include  "Includes/Configuration.include"
#pragma include  "Includes/LightCulling.include"

out vec4 result;

uniform sampler2D GBufferDepth;
uniform writeonly image2DArray cellGridFlags;

void main() {
    ivec2 coord = ivec2(gl_FragCoord.xy);
    float depth = texelFetch(GBufferDepth, coord, 0).x;
    ivec3 tile = getCellIndex(coord, depth);
    imageStore(cellGridFlags, tile, vec4(1));
    result.xyz = vec3(tile / vec3(LC_TILE_AMOUNT_X, LC_TILE_AMOUNT_Y, LC_TILE_SLICES));
    result.w = 1.0;
}