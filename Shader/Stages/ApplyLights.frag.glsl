#version 400

#pragma include "Includes/Configuration.inc.glsl"

// Tell the lighting pipeline we are doing this in screen space, so gl_FragCoord
// is available.
#define IS_SCREEN_SPACE 1

#pragma include "Includes/LightCulling.inc.glsl"
#pragma include "Includes/PositionReconstruction.inc.glsl"
#pragma include "Includes/LightingPipeline.inc.glsl"
#pragma include "Includes/GBufferPacking.inc.glsl"

in vec2 texcoord;
out vec4 result;

uniform sampler2D GBufferDepth;

uniform sampler2D GBuffer0;
uniform sampler2D GBuffer1;
uniform sampler2D GBuffer2;

void main() {    

    ivec2 coord = ivec2(gl_FragCoord.xy);
    float depth = texelFetch(GBufferDepth, coord, 0).x;
    ivec3 tile = getCellIndex(coord, depth);

    if (tile.z >= LC_TILE_SLICES) {
        result = vec4(0);
        return;
    }

    Material m = unpack_material(GBufferDepth, GBuffer0, GBuffer1, GBuffer2);

    result.xyz = shade_material_from_tile_buffer(m, tile);
    result.w = 1.0;

    #if MODE_ACTIVE(METALLIC)
        result.xyz = vec3(m.metallic);
    #endif


    #if MODE_ACTIVE(BASECOLOR)
        result.xyz = vec3(m.diffuse);
    #endif


    #if MODE_ACTIVE(ROUGHNESS)
        result.xyz = vec3(m.roughness);
    #endif


    #if MODE_ACTIVE(SPECULAR)
        result.xyz = vec3(m.specular);
    #endif


    #if MODE_ACTIVE(NORMAL)
        result.xyz = vec3(m.normal * 0.5 + 0.5);
    #endif

}