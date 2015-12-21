#version 400

#pragma include "Includes/Configuration.inc.glsl"

uniform sampler2D SourceTex;
uniform sampler2D ShadedScene;
uniform sampler2D SumTex;

in vec2 texcoord;
out vec4 result;

uniform bool FirstUpsamplePass;
uniform bool LastUpsamplePass;

void main() {

    vec3 summed = textureLod(SumTex, texcoord, 0).xyz;

    if (FirstUpsamplePass) {
        summed = vec3(0);
    }

    // upsample texture


    vec2 source_size = vec2(textureSize(SourceTex, 0).xy);
    ivec2 coord = ivec2(gl_FragCoord.xy);

    vec2 flt_coord = vec2(coord) / (2.0 * source_size);
    vec2 texel_size = 0.5 / source_size; 

    vec3 source_sample = textureLod(SourceTex, flt_coord, 0).xyz * 4;

    source_sample += textureLod(SourceTex, flt_coord + vec2(  0,  1) * texel_size, 0).xyz * 2;
    source_sample += textureLod(SourceTex, flt_coord + vec2(  0, -1) * texel_size, 0).xyz * 2;
    source_sample += textureLod(SourceTex, flt_coord + vec2(  1,  0) * texel_size, 0).xyz * 2;
    source_sample += textureLod(SourceTex, flt_coord + vec2( -1,  0) * texel_size, 0).xyz * 2;

    source_sample += textureLod(SourceTex, flt_coord + vec2( -1, -1) * texel_size, 0).xyz * 1;
    source_sample += textureLod(SourceTex, flt_coord + vec2(  1, -1) * texel_size, 0).xyz * 1;
    source_sample += textureLod(SourceTex, flt_coord + vec2( -1,  1) * texel_size, 0).xyz * 1;
    source_sample += textureLod(SourceTex, flt_coord + vec2(  1,  1) * texel_size, 0).xyz * 1;
        
    source_sample /= 16.0;

    vec3 pass_result = summed + source_sample;

    if (LastUpsamplePass) {
        result = vec4(textureLod(ShadedScene, texcoord, 0).xyz + pass_result, 1);
    } else {
        result = vec4(pass_result, 1);
    }
}
