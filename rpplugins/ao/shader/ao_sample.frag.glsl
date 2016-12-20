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

#if HAVE_PLUGIN(sky_ao)
uniform sampler2D SkyAOHalfRes;

#pragma include "/$$rp/rpplugins/sky_ao/shader/sky_ao.inc.glsl"
#endif

out vec2 ao_result;

void main() {
    ao_result.x = compute_ao(ivec2(gl_FragCoord.xy) * 2);

    #if HAVE_PLUGIN(sky_ao)
        Material m = unpack_material(GBuffer, get_half_texcoord());
        ao_result.y = compute_sky_ao(m.position, m.normal, SKYAO_HIGH_QUALITY, ivec2(gl_FragCoord.xy) * 2);

    #else
        ao_result.y = 0;
    #endif
}
