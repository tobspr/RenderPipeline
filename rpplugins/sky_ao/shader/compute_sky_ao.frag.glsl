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
#pragma include "includes/poisson_disk.inc.glsl"
#pragma include "includes/noise.inc.glsl"

uniform sampler2D SkyAOHeight;
uniform vec3 SkyAOCapturePosition;

out vec4 result;

void main() {

    vec2 texcoord = get_half_texcoord();
    Material m = unpack_material(GBuffer, texcoord);

    const float film_size = 200.0 * 0.5;

    vec2 local_coord = (m.position.xy - SkyAOCapturePosition.xy) / film_size * 0.5 + 0.5;

    if (out_of_screen(local_coord)) {
        result = vec4(1);
        return;
    }

    // Blend ao
    float fade_scale = 0.05;
    float blend = 1.0;
    blend *= saturate(min(local_coord.x, local_coord.y) / fade_scale);
    blend *= saturate(min(1 - local_coord.x, 1 - local_coord.y) / fade_scale);


    const float ao_scale = 0.5; // xxx: make configurable
    const float radius = 3.0;

    float ref_z = m.position.z;
    const int num_samples = 32;
    float accum = 0.0;

    for (int i = 0; i < num_samples; ++i) {
        vec2 offcoord = local_coord + poisson_disk_2D_32[i] / 1024.0 * radius;
        float sample_z = textureLod(SkyAOHeight, offcoord, 0).x;
        accum += saturate(min(0.5, ao_scale * (sample_z - ref_z)));
    }

    accum /= num_samples;
    accum = 1 - accum;
    accum = mix(1, accum, blend);

    result = vec4(accum);
}
