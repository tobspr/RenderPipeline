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

#define USE_GBUFFER_EXTENSIONS
#pragma include "render_pipeline_base.inc.glsl"
#pragma include "includes/gbuffer.inc.glsl"

#pragma include "sky_ao.inc.glsl"


uniform sampler2D LowPrecisionNormals;
vec3 get_normal(vec2 coord) { return unpack_normal_unsigned(textureLod(LowPrecisionNormals, coord, 0).xy); }
vec3 get_normal(ivec2 coord) { return unpack_normal_unsigned(texelFetch(LowPrecisionNormals, coord, 0).xy); }


out float result;

void main() {
    vec2 texcoord = get_quarter_texcoord();
    Material m = unpack_material(GBuffer, texcoord);
    m.normal = get_normal(texcoord);
    result = compute_sky_ao(m.position, m.normal, SKYAO_HIGH_QUALITY, ivec2(gl_FragCoord.xy));
}
