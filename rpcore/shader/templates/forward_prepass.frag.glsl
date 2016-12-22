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

%defines%

#pragma include "render_pipeline_base.inc.glsl"
#pragma include "includes/vertex_output.struct.glsl"
#pragma include "includes/transforms.inc.glsl"
#pragma include "includes/light_culling.inc.glsl"

%includes%
%inout%

layout(location = 0) in VertexOutput vOutput;

#if OPT_ALPHA_TESTING
    uniform sampler2D p3d_Texture0;
#endif

uniform sampler2D SceneDepth;
uniform writeonly image2DArray RESTRICT FlaggedCells;

// XXX: Check if return is faster than discard;

void main() {
    #if OPT_ALPHA_TESTING
        // Alpha tested shadows. This seems to be quite expensive, so we are
        // only doing this for the objects which really need it (like trees)
        float sampled_alpha = texture(p3d_Texture0, vOutput.texcoord).w;
        if (sampled_alpha < 0.1)
            discard;
    #endif

    %alpha_test%

    // Manual depth test
    float gbuffer_depth = texelFetch(SceneDepth, ivec2(gl_FragCoord.xy), 0).x;
    if (gbuffer_depth < gl_FragCoord.z) {
        // Occluded, don't write
        discard;
    }

    #if 0
        // This prevents the effect compiler from emitting a warning about
        // a undefined hook.
        %material%
    #endif

    // Inject
    ivec2 coord = ivec2(gl_FragCoord.xy);
    float linear_depth = get_linear_z_from_z(gl_FragCoord.z);

    // Find the affected cell
    ivec3 tile = get_lc_cell_index(ivec2(gl_FragCoord.xy), linear_depth);

    // Mark the cell as used
    imageStore(FlaggedCells, tile, vec4(1));
    discard; // Prevent color write. XXX: Check if faster   
}
