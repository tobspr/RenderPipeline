#pragma once

#pragma optionNV (unroll all)

vec3 do_chromatic_aberration(sampler2D colortex, vec2 texcoord, float factor) {

    vec2 mid_coord = texcoord * 2.0 - 1.0;
    vec3 blurred = vec3(0);
    const int num_samples = GET_SETTING(ColorCorrection, chromatic_aberration_samples);

    float factor_base = saturate( pow(factor, 2.0) - 0.02 ) * GET_SETTING(ColorCorrection, chromatic_aberration_strength);

    vec2 mid_coord_r = mid_coord;
    vec2 mid_coord_g = mid_coord * (1-0.04*factor_base*0.5);
    vec2 mid_coord_b = mid_coord * (1-0.04*factor_base);

    vec2 blur_dir = normalize(mid_coord + 0.000001) / vec2(WINDOW_WIDTH, WINDOW_HEIGHT) * 25.0 * factor_base;


    for (int i = -num_samples; i <= num_samples; ++i) {
        vec2 offset = float(i) / num_samples * blur_dir;
        vec2 offcord_r = mid_coord_r + offset;
        vec2 offcord_g = mid_coord_g + offset;
        vec2 offcord_b = mid_coord_b + offset;
        blurred.r += textureLod(colortex, offcord_r*0.5+0.5, 0).r;
        blurred.g += textureLod(colortex, offcord_g*0.5+0.5, 0).g;
        blurred.b += textureLod(colortex, offcord_b*0.5+0.5, 0).b;
    }

    blurred /= 2.0 * num_samples + 1;



    return blurred;
}