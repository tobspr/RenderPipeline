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

#pragma include "render_pipeline_base.inc.glsl"
#pragma include "ao_common.inc.glsl"

out float result;

uniform int pixel_multiplier;
uniform sampler2D LowPrecisionNormals;
vec3 get_normal(vec2 coord) { return unpack_normal_unsigned(textureLod(LowPrecisionNormals, coord, 0).xy); }
vec3 get_normal(ivec2 coord) { return unpack_normal_unsigned(texelFetch(LowPrecisionNormals, coord, 0).xy); }


uniform isamplerBuffer InvalidPixelCounter;
uniform isamplerBuffer InvalidPixelBuffer;
layout(r8) uniform writeonly image2D DestTex;

void main() {
    const int width = 512;
    
    int index = int(gl_FragCoord.x) + int(gl_FragCoord.y) * width; 
    int max_entries = texelFetch(InvalidPixelCounter, 0).x;
    if (index >= max_entries)
        discard;

    int coord_data = texelFetch(InvalidPixelBuffer, index).x;
    int frag_x = coord_data & 0xFFFF;
    int frag_y = coord_data >> 16;

    vec2 texcoord = vec2(ivec2(frag_x, frag_y) * pixel_multiplier + 0.5) / SCREEN_SIZE;
    Material m = unpack_material(GBuffer, texcoord);
    m.normal = get_normal(texcoord);
    float result = compute_ao(ivec2(frag_x, frag_y));
    imageStore(DestTex, ivec2(frag_x, frag_y), vec4(result));
}
