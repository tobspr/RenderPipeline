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

#version 420

#pragma optionNV (unroll all)

#define USE_MAIN_SCENE_DATA
#pragma include "render_pipeline_base.inc.glsl"
#pragma include "includes/gbuffer.inc.glsl"
#pragma include "includes/brdf.inc.glsl"
#pragma include "includes/color_spaces.inc.glsl"

layout(location=0) out vec4 result;
layout(location=1) out vec3 result_position;

uniform sampler2D SourceTex;
uniform sampler2D MipChain;
uniform GBufferData GBuffer;

void main() {
    // Get sample coordinates
    ivec2 coord = ivec2(gl_FragCoord.xy);
    ivec2 bil_start_coord = get_bilateral_coord(coord);

    // Shift samples each frame
    int offs_x = MainSceneData.frame_index % 2;
    int offs_y = (MainSceneData.frame_index / 2) % 2;

    // bil_start_coord -= ivec2(offs_x, offs_y);

    vec2 texcoord = ((bil_start_coord * 2) + 0.5) / SCREEN_SIZE;

    // Get current pixel data
    float mid_depth = get_gbuffer_depth(GBuffer, coord);
    vec3 ws_normal = get_gbuffer_normal(GBuffer, coord);

    Material m = unpack_material(GBuffer, texcoord);

    if (is_skybox(m.position)) {
        result = vec4(0);
        return;
    }


    const float max_depth_diff = 0.001;

    float weights = 0.0;
    vec4 accum = vec4(0);

    // Controls how many other pixels should be taken into account, besides
    // of the 4 direct neighbors.
    const int search_radius = 0;

    vec3 view_vector = normalize(MainSceneData.camera_pos - m.position);
    vec4 avg_position = vec4(0);

    // Get reflection directory
    vec3 reflected_dir = get_reflection_vector(m, -view_vector);
    float roughness = get_effective_roughness(m);

    vec4 avg_intersection = vec4(0.0);

    // Accumulate all samples
    for (int x = -search_radius; x < 2 + search_radius; ++x) {
        for (int y = -search_radius; y < 2 + search_radius; ++y) {

            ivec2 source_coord = bil_start_coord + ivec2(x, y);
            // ivec2 screen_coord = source_coord * 2 + ivec2(offs_x, offs_y);
            ivec2 screen_coord = source_coord * 2;
            vec4 source_sample = texelFetch(SourceTex, source_coord, 0);

            // Skip empty samples, however take into account we have no data there, so
            // still increase the weight
            if (length_squared(source_sample.xy) < 0.01 || source_sample.w < 0.005) {
                // weights += 1.0;
                continue;
            }

            float sample_depth = get_gbuffer_depth(GBuffer, screen_coord);

            // Find depth of intersection pixel
            float intersection_depth = get_gbuffer_depth(GBuffer, source_sample.xy);

            // Get world space position of intersection pixel
            vec3 wp_dest_sample = calculate_surface_pos(intersection_depth, source_sample.xy);

            // Find distance and vector to intersection based on the pixels position
            float distance_to_intersection = 1e-5 + distance(wp_dest_sample, m.position);
            vec3 direction_to_sample = (wp_dest_sample - m.position) / distance_to_intersection;

            // Get the halfway vector
            vec3 h = normalize(view_vector + direction_to_sample);
            float NxH = saturate(dot(m.normal, h));

            float weight = clamp(brdf_distribution_ggx(NxH, 0.05 + roughness), 0.0, 1e5);

            // weight *= source_sample.z;

            weight *= 1 - saturate(abs(mid_depth - sample_depth) / max_depth_diff);

            // float mipmap = saturate(dot(reflected_dir, m.normal)) * 7.0;
            float mipmap = sqrt(roughness) * 2.0 * (distance_to_intersection * 0.4);
            mipmap = clamp(mipmap, 0.0, 5.0);

            // mipmap = 0; // xxx

            vec4 color_sample = textureLod(MipChain, source_sample.xy, mipmap);

            color_sample *= source_sample.z;

            // Fade out samples at the screen border
            // XXX: Do we really have to this per sample?
            const float border_fade = 0.05;
            float fade = 1.0;
            fade *= saturate(source_sample.x / border_fade) * saturate(source_sample.y / border_fade);
            fade *= saturate((1-source_sample.x) / border_fade) * saturate((1-source_sample.y) / border_fade);
            color_sample *= fade;

            accum += color_sample * weight;
            avg_intersection += vec4(source_sample.xyz, 1);
            weights += weight;
        }
    }

    if (weights < 1e-4) {
        accum = vec4(0);
    } else {
        accum /= weights;
    }

    // Take precision issues into account
    accum *= 1.0 + 1e-3;
    accum.w = saturate(accum.w);

    result = accum;

    result_position = avg_intersection.xyz / max(1e-3, avg_intersection.w);
}
