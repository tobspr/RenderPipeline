#version 430

#define USE_MAIN_SCENE_DATA
#pragma include "Includes/Configuration.inc.glsl"
#pragma include "Includes/LightCulling.inc.glsl"
#pragma include "Includes/PositionReconstruction.inc.glsl"

#define USE_GBUFFER_EXTENSIONS 1
#pragma include "Includes/GBuffer.inc.glsl"

uniform layout(r8) image2DArray cellGridFlags;

void main() {
    ivec2 coord = ivec2(gl_FragCoord.xy);

    // Get the distance to the camera
    vec3 surf_pos = get_world_pos_at(coord);
    float surf_dist = distance(MainSceneData.camera_pos, surf_pos);

    // Find the affected cell
    ivec3 tile = get_lc_cell_index(coord, surf_dist);

    // Skip cells which are out of bounds
    if (tile.z < LC_TILE_SLICES) {

        // Mark the cell as used
        imageStore(cellGridFlags, tile, vec4(1));
    }
}
