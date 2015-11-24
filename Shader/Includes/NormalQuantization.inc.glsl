#pragma once

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
