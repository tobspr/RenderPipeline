#version 430

#pragma include "Includes/Configuration.inc.glsl"
#pragma include "Includes/LightCulling.inc.glsl"
#pragma include "Includes/GBuffer.inc.glsl"

out vec4 result;

uniform GBufferData GBuffer;
uniform writeonly image2DArray cellGridFlags;

void main() {
    ivec2 coord = ivec2(gl_FragCoord.xy);
    float depth = get_gbuffer_depth(GBuffer, coord);
    ivec3 tile = getCellIndex(coord, depth);
    imageStore(cellGridFlags, tile, vec4(1));
    result.xyz = vec3(tile / vec3(LC_TILE_AMOUNT_X, LC_TILE_AMOUNT_Y, LC_TILE_SLICES));
    result.w = 1.0;
}
