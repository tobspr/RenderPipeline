#version 400


uniform sampler2D SourceTex;
out vec4 result;

void main() {

    vec2 texsize = vec2(textureSize(SourceTex, 0).xy);

    ivec2 coord_screen = ivec2(gl_FragCoord.xy) * 4;
    vec2 local_coord = (coord_screen+1.0) / texsize;
    vec2 pixel_offset = 2.0 / texsize;

    float lum0 = textureLod(SourceTex, local_coord, 0).x;
    float lum1 = textureLod(SourceTex, local_coord + vec2(pixel_offset.x, 0), 0).x;
    float lum2 = textureLod(SourceTex, local_coord + vec2(0, pixel_offset.y), 0).x;
    float lum3 = textureLod(SourceTex, local_coord + pixel_offset.xy, 0).x;        

    result = vec4( (lum0 + lum1 + lum2 + lum3) * 0.25 );
}