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


#pragma include "includes/transforms.inc.glsl"
#pragma include "includes/noise.inc.glsl"
#pragma include "includes/sampling_sequences.inc.glsl"
#pragma include "includes/matrix_ops.inc.glsl"
#pragma include "includes/bilateral_params.inc.glsl"

#pragma optionNV (unroll all)

uniform sampler2D LowPrecisionDepth;
uniform sampler2D LowPrecisionHalfresDepth;

#define USE_GBUFFER_EXTENSIONS 1
#pragma include "includes/gbuffer.inc.glsl"

float get_linear_depth_at(vec2 coord) {
    // return textureLod(LowPrecisionDepth, coord, 0).x;
    return textureLod(LowPrecisionHalfresDepth, coord, 0).x;
}


float compute_ao(ivec2 coord) {

    // Provide some variables to the kernel
    vec2 pixel_size = vec2(1.0) / SCREEN_SIZE;
    vec2 texcoord = (coord + 0.5) / SCREEN_SIZE;

    // Shader variables
    float pixel_distance = get_linear_depth_at(texcoord);

    if (pixel_distance > 1000.0) {
        return 1.0;
    }

    float t = float(MainSceneData.frame_index % (GET_SETTING(ao, clip_length))) / float(GET_SETTING(ao, clip_length));
    // t = 0;
    t += pixel_distance;

    vec2 seed = ivec2(gl_FragCoord.xy) % 16 + t;

    // vec3 noise_vec = rand_rgb(coord + 0.32343 * t);
    // float rotation_factor = M_PI * rand(coord) + t * TWO_PI;
    float scale_factor = mix(0.1, 1.5, abs(rand(seed * 0.273523 + 0.84234)));

    float hpr_x = rand(seed * 0.59834 + 0.62839) * TWO_PI;
    float hpr_y = rand(seed * 0.48234 + 0.59383) * TWO_PI;
    float hpr_z = rand(seed * 0.86342 + 0.91845) * TWO_PI;

    mat2 perturb_mat_2d = make_rotate_mat2(hpr_x);
    perturb_mat_2d *= make_scale_mat2(scale_factor);

    // Generate 3D perturbation matrix
    mat3 perturb_mat_3d = make_rotate_mat3(hpr_x, hpr_y, hpr_z);
    perturb_mat_3d *= make_scale_mat3(scale_factor);

    vec3 pixel_view_normal = get_view_normal(texcoord);
    vec3 pixel_view_pos = get_view_pos_at(texcoord);
    vec3 pixel_world_normal = get_gbuffer_normal(GBuffer, texcoord);

    float screen_scale = WINDOW_WIDTH / 800.0 * 1.5;
    float kernel_scale = 2.0 / pixel_distance * screen_scale;

    // Increase kernel scale at obligue angles
    vec3 view_dir = normalize(pixel_view_pos);
    float NxV = saturate(dot(view_dir, -pixel_view_normal));
    kernel_scale *= max(0.5, NxV);

    float result = 0.0;

    // Include the appropriate kernel
    #if ENUM_V_ACTIVE(ao, technique, SSAO)
        #pragma include "ssao.kernel.glsl"
    #elif ENUM_V_ACTIVE(ao, technique, HBAO)
        #pragma include "hbao.kernel.glsl"
    #elif ENUM_V_ACTIVE(ao, technique, SSVO)
        #pragma include "ssvo.kernel.glsl"
    #elif ENUM_V_ACTIVE(ao, technique, ALCHEMY)
        #pragma include "alchemy.kernel.glsl"
    #elif ENUM_V_ACTIVE(ao, technique, UE4AO)
        #pragma include "ue4ao.kernel.glsl"
    #else
        #error Unkown AO technique!
    #endif


    result = pow(result, 2 * GET_SETTING(ao, occlusion_strength));

    return result;
}
