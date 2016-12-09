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
#pragma include "includes/color_spaces.inc.glsl"
#pragma include "includes/noise.inc.glsl"

uniform sampler2D SunMask;
flat in vec2 sun_pos_tc;
flat in float godray_factor;
out float result;

void main() {
    vec2 texcoord = get_half_texcoord();

    // raymarch to sun and collect .. whatever
    int history = GET_SETTING(scattering, godrays_resolve_history);
    float time_seed = (MainSceneData.frame_index % history) / float(history);

    float jitter = rand(texcoord + time_seed);

    vec2 diff_vec = abs(sun_pos_tc - texcoord);
    float d = length(diff_vec * vec2(1.0, ASPECT_RATIO));

    int num_samples = clamp(int(d * 700.0), 16, GET_SETTING(scattering, godrays_max_samples));
    const float fade_factor = 20.0;

    float accum = 0.0;

    for (int i = 0; i < num_samples; ++i) {
        float t = (i + jitter) / float(num_samples - 1);
        vec2 sample_coord = mix(texcoord, sun_pos_tc, t);

        float sample_data = textureLod(SunMask, sample_coord, 0).x;
        accum += sample_data * saturate(fade_factor * (1 - t));
    }

    accum /= num_samples;
    accum = pow(accum, 0.5);
    accum = saturate(accum) * godray_factor;
    result = accum;

}
