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

#version 420

#pragma include "Includes/Configuration.inc.glsl"

uniform int CurrentLod;
uniform sampler2D SourceImage;
uniform writeonly image2D RESTRICT DestImage;

void main() {
    ivec2 coord = ivec2(gl_FragCoord.xy);
    ivec2 base_coord = coord * 2;

    // Fetch the 4 pixels from the higher mipmap
    vec2 v0 = texelFetch(SourceImage, base_coord + ivec2(0, 0), CurrentLod).xy;
    vec2 v1 = texelFetch(SourceImage, base_coord + ivec2(1, 0), CurrentLod).xy;
    vec2 v2 = texelFetch(SourceImage, base_coord + ivec2(0, 1), CurrentLod).xy;
    vec2 v3 = texelFetch(SourceImage, base_coord + ivec2(1, 1), CurrentLod).xy;

    // Compute the maximum and mimimum values
    float min_z = min( min(v0.x, v1.x), min(v2.x, v3.x) );
    float max_z = max( max(v0.y, v1.y), max(v2.y, v3.y) );

    // Store the values
    imageStore(DestImage, coord, vec4(min_z, max_z, 0.0, 0.0));
}
