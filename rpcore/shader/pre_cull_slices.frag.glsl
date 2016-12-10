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

layout(early_fragment_tests) in;

// This shader takes the list of all camera frustum lights, and evaluates whether they 
// are in the given slice

#pragma include "render_pipeline_base.inc.glsl"
#pragma include "includes/transforms.inc.glsl"
#pragma include "includes/light_culling.inc.glsl"
#pragma include "includes/light_data.inc.glsl"
#pragma include "includes/light_classification.inc.glsl"

uniform usamplerBuffer FrustumLights;
uniform isamplerBuffer FrustumLightsCount;

layout(r16ui) uniform writeonly uimageBuffer PerSliceLights;
layout(r32i) uniform iimageBuffer PerSliceLightsCount;

uniform samplerBuffer AllLightsData;

void main() {

    int slice = int(gl_FragCoord.x);

    int thread_offset = int(gl_FragCoord.y);
    int max_light_count = min(LC_MAX_LIGHTS, texelFetch(FrustumLightsCount, 0).x);

    float start_dist = get_distance_from_slice(slice);
    float end_dist = get_distance_from_slice(slice + 1);

    Frustum view_frustum = make_view_frustum(0, 0, SCREEN_SIZE_INT, start_dist, end_dist);

    // Check for all lights if they are in current slice
    for (int i = thread_offset; i < max_light_count; i += LC_SLICE_CULL_THREADS) {   
        int light_index = int(texelFetch(FrustumLights, i).x);

        LightData light_data = read_light_data(AllLightsData, light_index);
        bool visible = cull_light(light_data, view_frustum);

        // Uncomment to detect culling issues
        // visible = true;

        if (visible) {
            int num_rendered_lights = imageAtomicAdd(PerSliceLightsCount, slice, 1).x;
            imageStore(PerSliceLights, slice * LC_MAX_LIGHTS + num_rendered_lights, uvec4(light_index));
        }
    }
}
