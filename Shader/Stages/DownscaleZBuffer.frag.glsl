#version 420

#pragma include "Includes/Configuration.inc.glsl"

uniform layout(rg32f) image2D SourceImage;
uniform writeonly image2D RESTRICT DestImage;

void main() {
    ivec2 coord = ivec2(gl_FragCoord.xy);
    ivec2 base_coord = coord * 2;

    // Fetch the 4 pixels from the higher mipmap
    vec2 v0 = imageLoad(SourceImage, base_coord + ivec2(0, 0)).xy;
    vec2 v1 = imageLoad(SourceImage, base_coord + ivec2(1, 0)).xy;
    vec2 v2 = imageLoad(SourceImage, base_coord + ivec2(0, 1)).xy;
    vec2 v3 = imageLoad(SourceImage, base_coord + ivec2(1, 1)).xy;

    // Compute the maximum and mimimum values
    float min_z = min( min(v0.x, v1.x), min(v2.x, v3.x) );
    float max_z = max( max(v0.y, v1.y), max(v2.y, v3.y) );

    // Store the values
    imageStore(DestImage, coord, vec4(min_z, max_z, 0.0, 0.0));
}
