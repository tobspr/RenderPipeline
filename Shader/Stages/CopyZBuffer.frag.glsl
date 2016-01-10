#version 420

#define USE_MAIN_SCENE_DATA
#pragma include "Includes/Configuration.inc.glsl"
#pragma include "Includes/GBuffer.inc.glsl"

uniform GBufferData GBuffer;

uniform writeonly image2D RESTRICT DestTexture;

void main() {
    vec2 coord = get_texcoord();
    float source_depth = get_gbuffer_depth(GBuffer, coord);
    imageStore(DestTexture, ivec2(gl_FragCoord.xy), vec4(source_depth));
}
