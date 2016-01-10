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

#pragma once



#define USE_NORMAL_QUANTIZATION 0

// Normal Quantization as described in the cryengine paper:
// http://advances.realtimerendering.com/s2010/Kaplanyan-CryEngine3(SIGGRAPH%202010%20Advanced%20RealTime%20Rendering%20Course).pdf
// Page 39 to 49

#if USE_NORMAL_QUANTIZATION

    uniform sampler2D NormalQuantizationTex;

    vec3 normal_quantization(vec3 normal)
    {        
        normal = normalize(normal);
        vec3 normal_abs = abs(normal.xyz);
        float max_comp = max(normal_abs.x, max(normal_abs.y, normal_abs.z));
        vec2 cube_coord = normal_abs.z < max_comp ?
            (normal_abs.y < max_comp ? normal.yz : normal.xz) : normal.xy;
        cube_coord /= max_comp;    
        ivec2 face_offs = ivec2( (cube_coord + 1.0));
        cube_coord = cube_coord + 1;

        // look-up fitting length and scale the normal to get the best fit
        float fitting_scale = texture(NormalQuantizationTex, cube_coord).x;
        return fma(normal * fitting_scale, vec3(0.5), vec3(0.5));
    }

    vec3 normal_unquantization(vec3 normal) {
        return normalize(fma(normal, vec3(2.0), vec3(-1.0));
    }

#else

    vec3 normal_quantization(vec3 normal) {
        return normalize(normal);
    } 

    vec3 normal_unquantization(vec3 normal) {
        return normalize(normal);
    } 

#endif



/*

Normal packing as described in:
A Survey of Efficient Representations for Independent Unit Vectors
Source: http://jcgt.org/published/0003/02/01/paper.pdf

*/

// For each component of v, returns -1 if the component is < 0, else 1
vec2 sign_not_zero(vec2 v) {
    #if 1
        // Branch-Less version
        return fma(step(vec2(0.0), v), vec2(2.0), vec2(-1.0));
    #else
        // Version with branches (for GLSL < 4.00)
        return vec2(
            v.x >= 0 ? 1.0 : -1.0,
            v.y >= 0 ? 1.0 : -1.0
        );
    #endif
}

// Packs a 3-component normal to 2 channels using octahedron normals
vec2 pack_normal_octahedron(vec3 v) {
    #if 0
        // Version as proposed by the paper
        // Project the sphere onto the octahedron, and then onto the xy plane
        vec2 p = v.xy * (1.0 / (abs(v.x) + abs(v.y) + abs(v.z)));
        // Reflect the folds of the lower hemisphere over the diagonals
        return (v.z <= 0.0) ? ((1.0 - abs(p.yx))  * sign_not_zero(p)) : p;
    #else
        // Faster version using newer GLSL capatibilities
        v.xy /= dot(abs(v), vec3(1));
        
        #if 0
            // Version with branches
            if (v.z <= 0) v.xy = (1.0 - abs(v.yx)) * sign_not_zero(v.xy);
            return v.xy;
        #else
            // Branch-Less version
            return mix(v.xy, (1.0 - abs(v.yx)) * sign_not_zero(v.xy), step(v.z, 0.0));
        #endif
    #endif
}


// Unpacking from octahedron normals, input is the output from pack_normal_octahedron
vec3 unpack_normal_octahedron(vec2 packed_nrm) {
    #if 1
        // Version using newer GLSL capatibilities
        vec3 v = vec3(packed_nrm.xy, 1.0 - abs(packed_nrm.x) - abs(packed_nrm.y));
        #if 1
            // Version with branches, seems to take less cycles than the
            // branch-less version
            if (v.z < 0) v.xy = (1.0 - abs(v.yx)) * sign_not_zero(v.xy);
        #else
            // Branch-Less version
            v.xy = mix(v.xy, (1.0 - abs(v.yx)) * sign_not_zero(v.xy), step(v.z, 0));
        #endif

        return normalize(v);
    #else
        // Version as proposed in the paper. 
        vec3 v = vec3(packed_nrm, 1.0 - dot(vec2(1), abs(packed_nrm)));
        if (v.z < 0)
            v.xy = (vec2(1) - abs(v.yx)) * sign_not_zero(v.xy);
        return normalize(v);
    #endif
}
