/**
 * 
 * RenderPipeline
 * 
 * Copyright (c) 2014-2015 tobspr <tobias.springer1@gmail.com>
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

#version 420

#pragma optionNV (unroll all)

#define USE_MAIN_SCENE_DATA
#pragma include "Includes/Configuration.inc.glsl"
#pragma include "Includes/PositionReconstruction.inc.glsl"
#pragma include "Includes/PoissonDisk.inc.glsl"

flat in int instance;
out vec4 result;

uniform sampler2D Noise4x4;

// use the extended gbuffer api
#define USE_GBUFFER_EXTENSIONS 1
#pragma include "Includes/GBuffer.inc.glsl"

void main() {

    result = vec4(1, 0, 0, 1);

    // Provide some variables to the kernel
    vec2 screen_size = vec2(WINDOW_WIDTH, WINDOW_HEIGHT);
    vec2 pixel_size = vec2(1.0) / screen_size;

    int quad_x = instance % 2;
    int quad_y = instance / 2;

    ivec2 coord = (ivec2(gl_FragCoord.xy) * 4) % SCREEN_SIZE_INT;
    coord += ivec2(quad_x, quad_y) * 2;

    vec2 texcoord = (coord + 0.5) / SCREEN_SIZE;

    // Shader variables
    float pixel_depth = get_depth_at(texcoord);
    vec3 pixel_view_pos = get_view_pos_at(texcoord);
    vec3 pixel_view_normal = get_view_normal(texcoord);
    vec3 pixel_world_pos = get_world_pos_at(texcoord);
    vec3 pixel_world_normal = get_gbuffer_normal(GBuffer, texcoord);

    vec3 view_vector = normalize(pixel_world_pos - MainSceneData.camera_pos);
    float view_dist = distance(pixel_world_pos, MainSceneData.camera_pos);

    vec3 noise_vec = fma(texelFetch(Noise4x4, 1 + ivec2(quad_x, quad_y), 0).xyz, vec3(2), vec3(-1));

    if (view_dist > 10000.0) {
        result = vec4(1);
        return;
    }

    // float kernel_scale = 10.0 / get_linear_z_from_z(pixel_depth);
    float kernel_scale = 10.0 / view_dist;

    // Include the appropriate kernel
    #if ENUM_V_ACTIVE(AO, technique, SSAO)
        #pragma include "../SSAO.kernel.glsl"
    #elif ENUM_V_ACTIVE(AO, technique, HBAO)
        #pragma include "../HBAO.kernel.glsl"
    #elif ENUM_V_ACTIVE(AO, technique, SSVO)
        #pragma include "../SSVO.kernel.glsl"
    #elif ENUM_V_ACTIVE(AO, technique, ALCHEMY)
        #pragma include "../ALCHEMY.kernel.glsl"
    #elif ENUM_V_ACTIVE(AO, technique, UE4AO)
        #pragma include "../UE4AO.kernel.glsl"
    #else
        #error Unkown AO technique!
    #endif

    result.w = pow(result.w, GET_SETTING(AO, occlusion_strength));

    // Pack bent normal
    result.xyz = fma(result.xyz, vec3(0.5), vec3(0.5));
}


