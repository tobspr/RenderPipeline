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

#version 400

#pragma include "Includes/Configuration.inc.glsl"

in vec4 p3d_Vertex;
out vec2 texcoord;
flat out int instance;

void main() {
    int x = gl_InstanceID % 2;
    int y = gl_InstanceID / 2;

    CONST_ARRAY float rotations[4] = float[4](180, 270, 90, 0);

    // Rotate the vertices because we use oversized triangles
    float rotation = degree_to_radians(rotations[gl_InstanceID]);

    vec2 vtx_pos = rotate(p3d_Vertex.xz, rotation);
    texcoord = fma(vtx_pos, vec2(0.5), vec2(0.5));
    vtx_pos.xy = fma(vtx_pos.xy, vec2(0.5), vec2(-0.5)) + vec2(x, y);

    instance = gl_InstanceID;
    gl_Position = vec4(vtx_pos, 0, 1);
}
