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
#pragma include "includes/poisson_disk.inc.glsl"

uniform samplerCubeArray SourceTex;
uniform writeonly imageCubeArray RESTRICT DestTex;
uniform int currentMip;
uniform int currentIndex;
out vec4 result;

void main() {

    // Get cubemap coordinate
    int texsize = textureSize(SourceTex, currentMip).x;
    ivec2 coord = ivec2(gl_FragCoord.xy);
    ivec2 clamped_coord; int face;
    vec3 n = texcoord_to_cubemap(texsize, coord, clamped_coord, face);


    const uint num_samples = 64;

    // Get tangent and binormal
    vec3 tangent, binormal;
    find_arbitrary_tangent(n, tangent, binormal);

    const float filter_radius = 0.00 + currentMip * 0.03;
    vec4 accum = vec4(0.0);
    for (uint i = 0; i < num_samples; ++i) {
        vec2 offset = poisson_disk_2D_64[i];
        vec3 sample_vec = normalize(n +
            filter_radius * offset.x * tangent +
            filter_radius * offset.y * binormal);
        accum += textureLod(SourceTex, vec4(sample_vec, currentIndex), 0);
    }
    accum /= float(num_samples);
    imageStore(DestTex, ivec3(clamped_coord, currentIndex * 6 + face), accum);
    result = accum;
}
