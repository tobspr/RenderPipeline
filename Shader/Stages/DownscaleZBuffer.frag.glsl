#version 420

#pragma include "Includes/Configuration.inc.glsl"

// uniform sampler2D GBufferDepth;
uniform layout(rg32f) image2D SourceImage;
uniform writeonly image2D DestImage;

// uniform layout(rg32f) image2D DestTexture;

void main() {
    ivec2 coord = ivec2(gl_FragCoord.xy);

    ivec2 basecoord = coord * 2;



    vec2 v0 = imageLoad(SourceImage, basecoord).xy;
    vec2 v1 = imageLoad(SourceImage, basecoord + ivec2(1, 0)).xy;
    vec2 v2 = imageLoad(SourceImage, basecoord + ivec2(0, 1)).xy;
    vec2 v3 = imageLoad(SourceImage, basecoord + ivec2(1, 1)).xy;

    float min_z = min( min(v0.x, v1.x), min(v2.x, v3.x) );
    float max_z = max( max(v0.x, v1.x), max(v2.x, v3.x) );

    imageStore(DestImage, coord, vec4(min_z, min_z, 0.0, 0.0));


    // float source_depth = texelFetch(GBufferDepth, coord).x;
    // imageStore(DestTexture, coord, vec4(source_depth));
}
