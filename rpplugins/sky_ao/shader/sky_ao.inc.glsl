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
#pragma once

#pragma include "includes/sampling_sequences.inc.glsl"
#pragma include "includes/noise.inc.glsl"

uniform sampler2D SkyAOHeight;
uniform vec3 SkyAOCapturePosition;

#define SKYAO_LOW_QUALITY 0
#define SKYAO_HIGH_QUALITY 1

float compute_sky_ao(vec3 ws_position, vec3 ws_normal, int quality, ivec2 tc) {

    // Constants
    const int ao_map_resolution = GET_SETTING(sky_ao, resolution);
    const float radius = GET_SETTING(sky_ao, sample_radius);
    const float ao_multiplier = GET_SETTING(sky_ao, ao_multiplier);
    const float ao_bias = GET_SETTING(sky_ao, ao_bias);
    const float fade_scale = GET_SETTING(sky_ao, blend_factor);
    const float ao_map_scale = GET_SETTING(sky_ao, max_radius); // world space
    const float film_size = ao_map_scale * 0.5;

    vec2 local_coord = (ws_position.xy - SkyAOCapturePosition.xy) / film_size * 0.5 + 0.5;

    if (out_of_screen(local_coord)) {
        return 1.0;
    }

    float blend = compute_fade_factor(local_coord, fade_scale);

    // Factor to convert from tex-space to world-space
    const float tc_to_ws = ao_map_scale;

    float accum = 0.0;

    float jitter = rand(tc % 4) * 0.3;
    jitter *= 0;

    // Capture samples
    const int trace_steps = quality == SKYAO_HIGH_QUALITY ? GET_SETTING(sky_ao, trace_steps) : 4;
    START_ITERATE_SEQUENCE(sky_ao, sample_sequence, vec3 offset)

        offset = normalize(offset);
        offset = face_forward(offset, ws_normal);
        offset += ws_normal * 0.3; // Avoid flickering
        offset *= radius;
        offset /= float(trace_steps);

        bool any_hit = false;
        float hit_dist = 0.0;
        for (int k = 1; k <= trace_steps; ++k) {
            float d = k + jitter.x;
            vec3 pos = ws_position + offset * d;
            vec2 offcoord = (pos.xy - SkyAOCapturePosition.xy) / film_size * 0.5 + 0.5; // TODO: optimize 

            float sample_z = textureLod(SkyAOHeight, offcoord, 0).x;
            if (sample_z > pos.z + 0.1) {
                any_hit = true;
                hit_dist = d / float(trace_steps);
                break;
            }
        }

        if (any_hit)
            accum += 1 - hit_dist;

    END_ITERATE_SEQUENCE()

    NORMALIZE_SEQUENCE(sky_ao, sample_sequence, accum);

    accum = 1 - accum;
    accum = max(ao_bias, accum);
    accum = pow(accum, 3.0);
    accum = mix(1, accum, ao_multiplier);
    accum = mix(1, accum, blend);
    return accum;
}
