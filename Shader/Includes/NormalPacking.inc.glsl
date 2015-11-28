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

vec2 sign_not_zero(vec2 v) {
    return vec2((v.x >= 0.0) ? +1.0 : -1.0, (v.y >= 0.0) ? +1.0 : -1.0);
}

// Assume normalized input.  Output is on [-1, 1] for each component.
vec2 pack_normal_octrahedron(vec3 v) {

    #if 0
        // Project the sphere onto the octahedron, and then onto the xy plane
        vec2 p = v.xy * (1.0 / (abs(v.x) + abs(v.y) + abs(v.z)));
        // Reflect the folds of the lower hemisphere over the diagonals
        return (v.z <= 0.0) ? ((1.0 - abs(p.yx))  * sign_not_zero(p)) : p;
    #else
        v.xy /= dot(vec3(1), abs(v));
        if (v.z <= 0)
            v.xy = (1 - abs(v.yx)) * sign_not_zero(v.xy);
        return v.xy;
    #endif
}


// Unpacking from octrahedron normals
vec3 unpack_normal_octrahedron(vec2 e) {
    #if 1
        vec3 v = vec3(e.xy, 1.0 - abs(e.x) - abs(e.y));
        if (v.z < 0) v.xy = (1.0 - abs(v.yx)) * sign_not_zero(v.xy);
        return normalize(v);
    #else
        vec3 v = vec3(e, 1.0 - dot(vec2(1), abs(e)));
        if (v.z < 0)
            v.xy = (vec2(1) - abs(v.yx)) * sign_not_zero(v.xy);
        return normalize(v);
    #endif
}



