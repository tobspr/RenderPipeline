#version 430

#pragma include "Includes/Configuration.inc.glsl"
#pragma include "Includes/LightCulling.inc.glsl"
#pragma include "Includes/GBuffer.inc.glsl"
#pragma include "Includes/PositionReconstruction.inc.glsl"

out vec4 result;

uniform GBufferData GBuffer;
uniform writeonly image2DArray cellGridFlags;

uniform vec3 cameraPosition;

void main() {
    ivec2 coord = ivec2(gl_FragCoord.xy);
    float depth = get_gbuffer_depth(GBuffer, coord);

    vec3 surf_pos = calculate_surface_pos(depth, vec2(coord) / SCREEN_SIZE);
    float surf_dist = distance(cameraPosition, surf_pos);

    ivec3 tile = getCellIndex(coord, surf_dist);
    imageStore(cellGridFlags, tile, vec4(1));
    result.xyz = vec3(tile / vec3(LC_TILE_AMOUNT_X, LC_TILE_AMOUNT_Y, LC_TILE_SLICES));
    result.w = 1.0;
}
