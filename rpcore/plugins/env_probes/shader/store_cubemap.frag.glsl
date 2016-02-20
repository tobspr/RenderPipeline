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

uniform sampler2D SourceTex;
uniform writeonly imageCubeArray RESTRICT DestTex;
out vec4 result;

void main() {
    ivec2 coord = ivec2(gl_FragCoord.xy);
    int size = textureSize(SourceTex, 0).y;
    vec3 source_data = texelFetch(SourceTex, coord, 0).rgb;
    const int store_index = 0; // <-- TODO

    // Convert to local cubemap coordinate
    int offset = coord.x / size;
    coord.x = coord.x % size;
    float scene_mask = length(source_data) > 1e-5 ? 1.0 : 0.0;

    // Store color in cubemap array
    imageStore(DestTex, ivec3(coord.x, coord.y, store_index * 6 + offset), vec4(source_data, scene_mask));
    result = vec4(source_data, 1);
}
