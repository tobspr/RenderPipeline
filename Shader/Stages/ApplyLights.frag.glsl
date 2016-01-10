#version 420

#define USE_MAIN_SCENE_DATA
#pragma include "Includes/Configuration.inc.glsl"

// Tell the lighting pipeline we are doing this in screen space, so gl_FragCoord
// is available.
#define IS_SCREEN_SPACE 1

#pragma include "Includes/LightCulling.inc.glsl"
#pragma include "Includes/PositionReconstruction.inc.glsl"
#pragma include "Includes/LightingPipeline.inc.glsl"
#pragma include "Includes/GBuffer.inc.glsl"

out vec4 result;

uniform GBufferData GBuffer;

void main() {    

    // Extract material properties
    vec2 texcoord = get_texcoord();
    float depth = get_gbuffer_depth(GBuffer, texcoord);
    Material m = unpack_material(GBuffer);
    ivec3 tile = get_lc_cell_index(
        ivec2(gl_FragCoord.xy),
        distance(MainSceneData.camera_pos, m.position));

    // Don't shade pixels out of the shading range
    if (tile.z >= LC_TILE_SLICES) {
        result = vec4(0, 0, 0, 1);
        return;
    }

    // Apply all lights
    result.xyz = shade_material_from_tile_buffer(m, tile);
    result.w = 1.0;

    /*
    
    Various debugging modes for previewing materials
    
    */

    #if MODE_ACTIVE(DIFFUSE)
        result.xyz = vec3(m.basecolor);
    #endif

    #if MODE_ACTIVE(ROUGHNESS)
        result.xyz = vec3(m.roughness);
    #endif

    #if MODE_ACTIVE(SPECULAR)
        result.xyz = vec3(m.specular);
    #endif

    #if MODE_ACTIVE(NORMAL)
        result.xyz = vec3(m.normal);
    #endif

    #if MODE_ACTIVE(METALLIC)
        result.xyz = vec3(m.metallic);
    #endif

    #if MODE_ACTIVE(TRANSLUCENCY)
        result.xyz = vec3(m.translucency);
    #endif
}
