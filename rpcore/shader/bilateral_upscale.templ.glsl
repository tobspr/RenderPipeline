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

// Shader which upscales a half resolution image to full resolution,
// respecting the normals and depth

#pragma optionNV (unroll all)

#pragma include "render_pipeline_base.inc.glsl"
#pragma include "includes/gbuffer.inc.glsl"

uniform sampler2D SourceTex;
uniform GBufferData GBuffer;

// Template Configuration:
// SKIP_SKYBOX - Wheter to skip the skybox when scaling
// SKYBOX_COLOR - The color to write when skipping the skybox
// TRACK_INVALID_PIXELS - Whether to write invalid pixels to a given buffer

#if TRACK_INVALID_PIXELS
    layout(r32i) uniform iimageBuffer InvalidPixelCounter;
    layout(r32i) uniform writeonly iimageBuffer InvalidPixelBuffer;
#endif

#if HALF_RES
    #define MULTIPLIER 2
#else
    #define MULTIPLIER 1
#endif

uniform sampler2D LowPrecisionNormals;
vec3 get_normal(vec2 coord) { return unpack_normal_unsigned(textureLod(LowPrecisionNormals, coord, 0).xy); }
vec3 get_normal(ivec2 coord) { return unpack_normal_unsigned(texelFetch(LowPrecisionNormals, coord, 0).xy); }

out vec4 result;

void main() {
    // Get sample coordinates
    ivec2 coord = ivec2(gl_FragCoord.xy);
    ivec2 ss_coord = coord * MULTIPLIER;

    ivec2 bil_start_coord = get_bilateral_coord(coord);

    // Get current pixel data
    float mid_depth = get_gbuffer_depth(GBuffer, ss_coord);
    float mid_depth_linear = get_linear_z_from_z(mid_depth);
    vec3 mid_nrm = get_normal(ss_coord);

    #if SKIP_SKYBOX
        if (mid_depth_linear > SKYBOX_DIST) {
            result = SKYBOX_COLOR;
            return;
        }
    #endif

    vec3 pixel_pos = get_gbuffer_position(GBuffer, ss_coord);
    vec3 view_dir = normalize(pixel_pos - MainSceneData.camera_pos);

    float NxV = saturate(dot(view_dir, -mid_nrm));

    const float max_nrm_diff = 0.1;
    float max_depth_diff = mid_depth_linear / 50.0;
    max_depth_diff /= max(0.1, NxV);

    float weights = 0.0;
    vec4 accum = vec4(0);

    // Controls how many other pixels should be taken into account, besides
    // of the 4 direct neighbors.
    const int search_radius = 0;

    // TODO: On the bottom left pixels, do not check neighbours, can save 25% performance
    // with this

    // Accumulate all samples
    for (int x = -search_radius; x < 2 + search_radius; ++x) {
        for (int y = -search_radius; y < 2 + search_radius; ++y) {

            ivec2 source_coord = bil_start_coord + ivec2(x, y);
            vec4 source_sample = texelFetch(SourceTex, source_coord, 0);

            // Check how much information those pixels share, and if it is
            // enough, use that sample
            float sample_depth = get_gbuffer_depth(GBuffer, source_coord * 2 * MULTIPLIER);
            float sample_depth_linear = get_linear_z_from_z(sample_depth);
            float depth_diff = abs(sample_depth_linear - mid_depth_linear) > max_depth_diff ? 0.0 : 1.0;
            float weight = depth_diff;
            // weight = 1;
            vec3 sample_nrm = get_normal(source_coord * 2 * MULTIPLIER);
            float nrm_diff = distance(sample_nrm, mid_nrm) < max_nrm_diff ? 1.0 : 0.0;
            weight *= nrm_diff;

            accum += source_sample * weight;
            weights += weight;
            
        }
    }

    if (weights < 1e-5) {
        // When no sample was valid, take the center sample - this is still
        // better than invalid pixels
        result = texelFetch(SourceTex, coord / 2, 0);
        
        // Visualization to see failed resolves
        #if SPECIAL_MODE_ACTIVE(BILATERAL_MISSES)
            result *= 0;
        #else
            #if TRACK_INVALID_PIXELS
                int index = imageAtomicAdd(InvalidPixelCounter, 0, 1);
                int coord_masked = int(gl_FragCoord.x) | (int(gl_FragCoord.y) << 16);
                imageStore(InvalidPixelBuffer, index, ivec4(coord_masked));
            #endif
        #endif

    } else {
        result = accum / weights;
    }

}
