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

#pragma optionNV (unroll all)

#pragma include "render_pipeline_base.inc.glsl"
#pragma include "includes/transforms.inc.glsl"
#pragma include "includes/noise.inc.glsl"
#pragma include "includes/sampling_sequences.inc.glsl"
#pragma include "includes/matrix_ops.inc.glsl"

out vec2 result;

uniform sampler2D LowPrecisionDepth;
uniform sampler2D AOResult;

// use the extended gbuffer api
#define USE_GBUFFER_EXTENSIONS 1
#pragma include "includes/gbuffer.inc.glsl"

float get_linear_depth_at(vec2 coord) {
    return textureLod(LowPrecisionDepth, coord, 0).x;
}

void main() {
    ivec2 coord = ivec2(gl_FragCoord.xy);

    // Provide some variables to the kernel
    vec2 screen_size = vec2(WINDOW_WIDTH, WINDOW_HEIGHT);
    vec2 pixel_size = vec2(1.0) / screen_size;
    vec2 texcoord = get_texcoord();
    float pixel_z = get_linear_depth_at(texcoord);

    // Merge with previous ao result
    vec2 prev_result = textureLod(AOResult, texcoord, 0).xy;

    // Fade out small scale ao at great distances
    if (pixel_z > 50.0) {
        result = prev_result;
        return;
    }

    // Compute noise components
    float t = float(MainSceneData.frame_index % (GET_SETTING(ao, clip_length))) / float(GET_SETTING(ao, clip_length));
    t = 0; // XXX
    
    float rotation_factor = M_PI * rand(coord % 256) + t * TWO_PI;
    mat2 rotation_mat = make_rotate_mat2(rotation_factor);
    float scale_factor = mix(0.5, 1.05, abs(rand(coord % 32 + 0.05 * t)));
    vec3 noise_vec = rand_rgb(coord % 4 +
        0.01 * (MainSceneData.frame_index % (GET_SETTING(ao, clip_length))));

    // Determina AO params
    vec3 pixel_view_normal = get_view_normal(texcoord);
    vec3 pixel_view_pos = get_view_pos_at(texcoord);

    // float kernel_scale = 10.0 / pixel_z;
    float kernel_scale = 0.8;
    const float sample_radius = 6.0;

    const int num_samples = 4;
    const float bias = 0.0005 + 0.001 * pixel_z;

    float max_range = GET_SETTING(ao, sc_occlusion_max_dist) * 5;

    float sample_offset = sample_radius * pixel_size.x * 5 * GET_SETTING(ao, sc_occlusion_range);
    float range_accum = 0.0;
    float accum = 0.0;

    sample_offset /= kernel_scale;
    sample_offset *= scale_factor;

    // Collect samples
    for (int i = 0; i < num_samples; ++i) {
        vec3 offset = halton_3D_4[i];

        offset.xy = rotation_mat * offset.xy;

        // Since poisson disks have more samples to the outer, but this
        // does not match the ao definition, move the samples closer to the pixel
        offset = pow(abs(offset), vec3(2.0)) * sign(offset);

        // Flip offset in case it faces away from the normal
        offset = face_forward(offset, pixel_view_normal);

        // Compute offset position in view space
        vec3 offset_pos = pixel_view_pos + offset * sample_offset;

        // Project offset position to screen space
        vec3 projected = view_to_screen(offset_pos);

        if (!in_unit_box(projected))
            continue;

        // Fetch the expected depth
        float sample_depth = get_linear_depth_at(projected.xy);

        // Linearize both depths
        float linz_a = get_linear_z_from_z(projected.z);
        float linz_b = sample_depth;

        // Compare both depths by distance to find the AO factor
        float modifier = step(distance(linz_a, linz_b), max_range * 0.2);
        range_accum += fma(modifier, 0.5, 0.5);
        modifier *= step(linz_b + bias, linz_a);
        accum += modifier;
    }

    // Normalize samples
    accum /= max(0.01, range_accum);
    accum = 1 - accum;
    accum = pow(accum, 3 * GET_SETTING(ao, sc_occlusion_strength));


    #if !MODE_ACTIVE(OCCLUSION)
        // prev_result.x *= accum;
    #endif

    #if MODE_ACTIVE(SC_OCCLUSION)
        prev_result.x = accum;
    #endif


    // Fade out AO at obligue angles
    // vec3 view_dir = normalize(pixel_view_pos);
    // float NxV = saturate(dot(view_dir, -pixel_view_normal));
    // float fade = 1 - saturate(4 * NxV);
    // fade = 0;
    float fade = 0;

    prev_result.x = prev_result.x * (1 - fade) + fade;
    result = prev_result;
}
