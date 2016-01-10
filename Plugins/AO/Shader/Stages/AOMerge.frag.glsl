/**
 * 
 * RenderPipeline
 * 
 * Copyright (c) 2014-2015 tobspr <tobias.springer1@gmail.com>
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

#version 400

#pragma include "Includes/Configuration.inc.glsl"

uniform sampler2D SourceTex;
out vec4 result;

vec4 unpack_ao(vec4 data) {
    return vec4(
        normalize(fma(data.xyz, vec3(2.0), vec3(-1.0))),
        data.w
    );
}

void main() {
    ivec2 coord = ivec2(gl_FragCoord.xy);
    const ivec3 half_size = ivec3(SCREEN_SIZE_INT / 2, 0);

    vec4 accum = vec4(0);
    accum += unpack_ao(texelFetch(SourceTex, coord + half_size.zz, 0));
    accum += unpack_ao(texelFetch(SourceTex, coord + half_size.xz, 0));
    accum += unpack_ao(texelFetch(SourceTex, coord + half_size.zy, 0));
    accum += unpack_ao(texelFetch(SourceTex, coord + half_size.xy, 0));
    accum /= 4.0;
    result = vec4(fma(normalize(accum.xyz), vec3(0.5), vec3(0.5)), accum.w);
}
