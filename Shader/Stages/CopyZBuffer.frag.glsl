#version 420

#pragma include "Includes/Configuration.inc.glsl"

uniform sampler2D GBufferDepth;

uniform layout(rg32f) image2D DestTexture;

void main() {
    ivec2 coord = ivec2(gl_FragCoord.xy);
    float source_depth = texelFetch(GBufferDepth, coord, 0).x;
    imageStore(DestTexture, coord, vec4(source_depth));
}
