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

// This shader takes the list of all lights, and evaluates whether they are
// in the camera frustum. This improves the performance of the actual culling
// pass.

#pragma include "render_pipeline_base.inc.glsl"
#pragma include "includes/transforms.inc.glsl"
#pragma include "includes/light_culling.inc.glsl"
#pragma include "includes/light_data.inc.glsl"
#pragma include "includes/light_classification.inc.glsl"

uniform writeonly uimageBuffer FrustumLights;
layout(r32i) uniform iimageBuffer FrustumLightsCount;

uniform samplerBuffer AllLightsData;
uniform int maxLightIndex;

void main() {

    const int tile_size = 16;
    ivec2 coord = ivec2(gl_FragCoord.xy);

    int start_offset = coord.y * tile_size + coord.x;
    
    Frustum view_frustum = make_view_frustum(0, 0, ivec2(1, 1), 0.0, LC_MAX_DISTANCE);

    // Check for all lights if they are in the view frustum, to reduce load
    // on the upcoming detailed culling pass
    for (int i = start_offset; i < maxLightIndex + 1; i += tile_size * tile_size) {
        LightData light_data = read_light_data(AllLightsData, i);

        // XXX: Might first read the type, then skip early
        int light_type = get_light_type(light_data);

        // Skip Null-Lights
        if (light_type < 1) continue;

        bool visible = cull_light(light_data, view_frustum);

        if (visible) {
            int index = imageAtomicAdd(FrustumLightsCount, 0, 1);
            imageStore(FrustumLights, index, uvec4(i));
        }
    }
}
