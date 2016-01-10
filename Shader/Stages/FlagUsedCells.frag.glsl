#version 430

#define USE_MAIN_SCENE_DATA
#pragma include "Includes/Configuration.inc.glsl"
#pragma include "Includes/LightCulling.inc.glsl"
#pragma include "Includes/PositionReconstruction.inc.glsl"

#define USE_GBUFFER_EXTENSIONS 1
#pragma include "Includes/GBuffer.inc.glsl"

uniform writeonly image2DArray RESTRICT cellGridFlags;

void main() {
    vec2 texcoord = get_texcoord();

    // Get the distance to the camera
    vec3 surf_pos = get_world_pos_at(texcoord);
    float surf_dist = distance(MainSceneData.camera_pos, surf_pos);

    // Find the affected cell
    ivec3 tile = get_lc_cell_index(ivec2(gl_FragCoord.xy), surf_dist);

    // Mark the cell as used
    imageStore(cellGridFlags, tile, vec4(1));
}
