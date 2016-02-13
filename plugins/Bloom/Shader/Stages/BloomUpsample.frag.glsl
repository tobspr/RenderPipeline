/**
 *
 * RenderPipeline
 *
 * Copyright (c) 2014-2016 tobspr <tobias.springer1@gmail.com>
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 * THE SOFTWARE.
 *
 */

#version 430

#pragma include "Includes/Configuration.inc.glsl"

uniform int SourceMip;
uniform sampler2D SourceTex;
uniform writeonly image2D RESTRICT DestTex;

uniform sampler2D ShadedScene;
uniform sampler2D SumTex;

out vec4 result;

uniform bool FirstUpsamplePass;
uniform bool LastUpsamplePass;

void main() {
    vec2 source_size = vec2(textureSize(SourceTex, SourceMip).xy);
    vec2 texcoord = (ivec2(gl_FragCoord.xy) + 0.5) / (2.0 * source_size);
    vec3 summed = textureLod(SourceTex, texcoord, SourceMip + 1).xyz;

    if (FirstUpsamplePass) {
        summed = vec3(0);
    }

    // upsample texture
    ivec2 coord = ivec2(gl_FragCoord.xy);

    vec2 flt_coord = vec2(coord) / (2.0 * source_size);
    vec2 texel_size = 1.0 / source_size;

    vec3 source_sample = textureLod(SourceTex, flt_coord, SourceMip).xyz * 4;

    source_sample += textureLod(SourceTex, flt_coord + vec2(  0,  1) * texel_size, SourceMip).xyz * 2;
    source_sample += textureLod(SourceTex, flt_coord + vec2(  0, -1) * texel_size, SourceMip).xyz * 2;
    source_sample += textureLod(SourceTex, flt_coord + vec2(  1,  0) * texel_size, SourceMip).xyz * 2;
    source_sample += textureLod(SourceTex, flt_coord + vec2( -1,  0) * texel_size, SourceMip).xyz * 2;

    source_sample += textureLod(SourceTex, flt_coord + vec2( -1, -1) * texel_size, SourceMip).xyz * 1;
    source_sample += textureLod(SourceTex, flt_coord + vec2(  1, -1) * texel_size, SourceMip).xyz * 1;
    source_sample += textureLod(SourceTex, flt_coord + vec2( -1,  1) * texel_size, SourceMip).xyz * 1;
    source_sample += textureLod(SourceTex, flt_coord + vec2(  1,  1) * texel_size, SourceMip).xyz * 1;

    source_sample /= 16.0;

    vec3 pass_result = summed + source_sample;

    vec4 old_data = texelFetch(SourceTex, coord, SourceMip - 1);
    imageStore(DestTex, coord, old_data + vec4(pass_result, 0));

    if (LastUpsamplePass) {
        result = vec4(textureLod(ShadedScene, texcoord, 0).xyz + pass_result, 1);
    }
}
