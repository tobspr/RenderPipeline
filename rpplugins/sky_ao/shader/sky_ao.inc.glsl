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
#pragma include "includes/matrix_ops.inc.glsl"

uniform sampler2D SkyAOHeight;
uniform vec3 SkyAOCapturePosition;

#define SKYAO_LOW_QUALITY 0
#define SKYAO_HIGH_QUALITY 1

const float film_size = GET_SETTING(sky_ao, max_radius) * 0.5;

float compute_sky_ao(vec3 ws_position, vec3 ws_normal, const int quality, ivec2 tc) {

    vec2 local_coord = (ws_position.xy - SkyAOCapturePosition.xy) / film_size * 0.5 + 0.5;

    if (!in_unit_rect(local_coord)) {
        return 1.0;
    }

    float blend = compute_fade_factor(local_coord, GET_SETTING(sky_ao, blend_factor));
    float accum = 0.0;

    ivec2 seed = tc % 4 + 5;
    if (quality == SKYAO_HIGH_QUALITY) {
        seed.x += 10 + 734 * (MainSceneData.frame_index % max(1, GET_SETTING(ao, clip_length) / 4));
    }
    
    float noise_amount = GET_SETTING(sky_ao, noise_amount);
    float jitter = rand(seed * 0.23423 + 0.96344) * 0.9;
    float rot_x  = rand(seed * 0.63452 + 0.45343) * noise_amount;
    float rot_y  = rand(seed * 0.96343 + 0.95433) * noise_amount;
    float rot_z  = rand(seed * 0.18643 + 0.13234) * noise_amount;

    mat3 combined_rotation = make_rotate_mat3(rot_x, rot_y, rot_z);

    if (quality != SKYAO_HIGH_QUALITY) {
        combined_rotation = make_ident_mat3();
        jitter *= 0;
    }

    // Capture samples
    const int trace_steps = quality == SKYAO_HIGH_QUALITY ? GET_SETTING(sky_ao, trace_steps) : 4;
    const float position_bias = 0.1;

    START_ITERATE_SEQUENCE(sky_ao, sample_sequence, vec3 offset)

        offset *= combined_rotation;
        offset = normalize(offset);
        offset = face_forward(offset, ws_normal);
        offset += ws_normal * GET_SETTING(sky_ao, normal_offset); // Avoid flickering
        offset *= GET_SETTING(sky_ao, sample_radius) / float(trace_steps);

        bool any_hit = false;
        float hit_dist = 0.0;
        for (int k = 1; k <= trace_steps; ++k) {
            float d = k + jitter.x;
            vec3 pos = ws_position + offset * d;
            vec2 offcoord = (pos.xy - SkyAOCapturePosition.xy) / film_size * 0.5 + 0.5; // TODO: optimize 

            float sample_z = textureLod(SkyAOHeight, offcoord, 0).x;
            if (sample_z > pos.z + position_bias) {
                any_hit = true;
                hit_dist = d / float(trace_steps);
                break;
            }
        }

        if (any_hit)
            accum += 1.0 - hit_dist;

    END_ITERATE_SEQUENCE()
    NORMALIZE_SEQUENCE(sky_ao, sample_sequence, accum);

    // XXX: TODO: Merge into single expression
    accum = 1.0 - accum;
    accum = max(GET_SETTING(sky_ao, ao_bias), accum);
    accum = pow(accum, 5.0);
    accum = mix(1.0, accum, float(GET_SETTING(sky_ao, ao_multiplier)));
    accum = mix(1.0, accum, blend);
    accum = pow(accum, 3.0);
    return accum;
}
