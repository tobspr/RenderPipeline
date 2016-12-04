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

#pragma optionNV (unroll all)

uniform sampler2D DownscaledDepth;

#define USE_GBUFFER_EXTENSIONS 1
#pragma include "includes/gbuffer.inc.glsl"

float get_linear_depth_at(vec2 coord) {
    return textureLod(DownscaledDepth, coord, 0).x;
    // return get_linear_z_from_z(textureLod(GBuffer.Depth, coord, 0).x);
}


float compute_ao(ivec2 coord_fullres) {

    // Provide some variables to the kernel
    vec2 pixel_size = vec2(1.0) / SCREEN_SIZE;

    ivec2 coord = coord_fullres;
    vec2 texcoord = (coord + 0.5) / SCREEN_SIZE;

    // Shader variables
    float pixel_depth = get_depth_at(texcoord);
    float pixel_distance = get_linear_z_from_z(pixel_depth);

    if (pixel_distance > 1000.0) {
        return 1.0;
    }

    float t = float(MainSceneData.frame_index % (GET_SETTING(ao, clip_length))) / float(GET_SETTING(ao, clip_length));
    // t = 0;

    t += pixel_distance;

    vec3 noise_vec = rand_rgb(coord + 0.32343 * t);
    float rotation_factor = M_PI * rand(coord) + t * TWO_PI;
    float scale_factor = mix(0.8, 1.2, abs(rand(coord + 0.1 * t)));

    // rotation_factor = 0;
    // scale_factor = 1;


    mat2 rotation_mat = make_rotate_mat2(rotation_factor);

    vec3 pixel_view_normal = get_view_normal(texcoord);
    vec3 pixel_view_pos = get_view_pos_at(texcoord);
    vec3 pixel_world_normal = get_gbuffer_normal(GBuffer, texcoord);

    float kernel_scale = 10.0 / pixel_distance;
    // float kernel_scale = 10.0 / sqrt(pixel_distance) * 0.3;
    // float kernel_scale = 1.2;

    // Increase kernel scale at obligue angles
    vec3 view_dir = normalize(pixel_view_pos);
    float NxV = saturate(dot(view_dir, -pixel_view_normal));
    // kernel_scale *= max(0.5, NxV);

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

    result = pow(saturate(result), GET_SETTING(ao, occlusion_strength));
    
    // Increase AO in the distance
    float pow_add = pixel_distance / 400.0;
    
    result = pow(result, 3.0 + pow_add);


    return result;
}
