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
#pragma include "includes/importance_sampling.inc.glsl"

// #pragma optionNV (unroll all)

uniform samplerCube SourceTex;
uniform writeonly imageCubeArray RESTRICT DestTex;
uniform int currentIndex;
out vec4 result;

vec4 get_sample(vec3 dir, vec3 n, inout float accum_weight) {
    vec3 v = face_forward(dir, n);
    vec4 data = textureLod(SourceTex, v, 0);
    float weight = max(0, dot(v, n));
    accum_weight += weight;
    return data * weight;
}

void main() {
    // Get cubemap coordinate
    const int texsize = GET_SETTING(env_probes, diffuse_probe_resolution);
    ivec2 coord = ivec2(gl_FragCoord.xy);
    ivec2 clamped_coord; int face;
    vec3 n = texcoord_to_cubemap(texsize, coord, clamped_coord, face);

    // Get tangent and binormal
    vec3 tangent, binormal;
    find_arbitrary_tangent(n, tangent, binormal);

    const int num_samples = 256;
    vec4 accum = vec4(0.0);
    for (uint i = 0; i < num_samples; ++i) {
        vec2 Xi = hammersley(i, num_samples);
        vec3 h = importance_sample_lambert(Xi);
        h = normalize(h.x * tangent + h.y * binormal + h.z * n);

        // Reconstruct light vector
        vec3 l = -reflect(n, h);
        accum += textureLod(SourceTex, l, 0);
    }
    accum /= num_samples;
    imageStore(DestTex, ivec3(clamped_coord, currentIndex * 6 + face), accum);
    result = accum;
}
