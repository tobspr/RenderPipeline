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

#pragma include "render_pipeline_base.inc.glsl"

uniform sampler2D ShadedScene;
uniform sampler2D BlurredShadedScene;
uniform sampler2D SceneDepth;

uniform samplerBuffer ForwardFragmentData;
uniform samplerBuffer ForwardFragmentDepth;
uniform usamplerBuffer ForwardFragmentNext;
uniform usampler2D ForwardLinkedListHead;

out vec3 result;

struct Fragment {
    float depth;
    vec4 color;
    float roughness;
    uint next;
};

Fragment get_fragment(uint frag_index) {
    int index = int(frag_index);
    Fragment frag;
    frag.depth = texelFetch(ForwardFragmentDepth, index).x;
    frag.color = texelFetch(ForwardFragmentData, index);
    frag.roughness = int(frag.color.w) / 255.0;
    frag.color.w = mod(frag.color.w, 1.0);
    frag.next = texelFetch(ForwardFragmentNext, index).x;
    return frag;
}

#define MAX_FRAGMENTS 4

void main() {
    ivec2 coord = ivec2(gl_FragCoord.xy);
    vec2 texcoord = get_texcoord();

    vec3 scene_color = textureLod(ShadedScene, texcoord, 0).xyz;
    uint list_head = texelFetch(ForwardLinkedListHead, coord, 0).x;

    if (list_head == 0) {
        result = scene_color;
        return;
    }

    float pixel_depth = texelFetch(SceneDepth, coord, 0).x;

    // Read in all fragments
    Fragment fragments[MAX_FRAGMENTS];
    uint fragment_array[MAX_FRAGMENTS];
    int num_fragments = 0;
    uint ptr = list_head;

    // Iterate over linked list, but make sure we produce no endless loop
    int max_iter = 50;
    
    // Also store max roughness to detect texture filtering level
    float max_roughness = 0.0;

    while(num_fragments < (MAX_FRAGMENTS - 1) && ptr != 0 && max_iter --> 0) {
        Fragment frag = get_fragment(ptr);
        ptr = frag.next;

        fragments[num_fragments] = frag; 
        fragment_array[num_fragments] = num_fragments;
        ++num_fragments;
        max_roughness = max(max_roughness, frag.roughness);
    }


    // Insertion sort
    // XXX: Use more performant solution like backwards memory allocation
    for (uint i = 1; i <= num_fragments - 1; ++i) {
        uint d = i;
        while (d > 0 && fragments[fragment_array[d]].depth > fragments[fragment_array[d - 1]].depth) {
            uint temp = fragment_array[d];
            fragment_array[d] = fragment_array[d - 1];
            fragment_array[d - 1] = temp;
            d--;
        }

    }

    // Apply fragments
    vec3 curr_color = textureLod(BlurredShadedScene, texcoord, 0).xyz;

    if (max_roughness < 0.01) {
        curr_color = scene_color;
    }

    for (uint i = 0; i < num_fragments; ++i) {
        Fragment f = fragments[fragment_array[i]];
        vec3 transmittance = vec3(1); // XXX: Allow specifying transmittance
        curr_color = curr_color * transmittance * (1 - f.color.w) + f.color.xyz;
    }

    result = curr_color;

}
