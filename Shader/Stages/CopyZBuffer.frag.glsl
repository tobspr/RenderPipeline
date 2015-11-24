#version 420

#pragma include "Includes/Configuration.inc.glsl"
#pragma include "Includes/GBuffer.inc.glsl"

uniform GBufferData GBuffer;

uniform layout(rg32f) image2D DestTexture;

void main() {
    ivec2 coord = ivec2(gl_FragCoord.xy);
    float source_depth = get_gbuffer_depth(GBuffer, coord);
    imageStore(DestTexture, coord, vec4(source_depth));
}
