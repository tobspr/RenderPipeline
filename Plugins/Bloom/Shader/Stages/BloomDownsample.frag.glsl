#version 430

#pragma include "Includes/Configuration.inc.glsl"

in vec2 texcoord;

uniform int SourceMip;
uniform sampler2D SourceTex;
uniform restrict writeonly image2D DestTex;

void main() {
    ivec2 int_coord = ivec2(gl_FragCoord.xy);
    vec2 parent_tex_size = vec2(textureSize(SourceTex, SourceMip).xy);
    vec2 texel_size = 1.0 / parent_tex_size;

    // Compute the floating point coordinate pointing to the exact center of the 
    // parent texel center
    vec2 flt_coord = vec2(int_coord + 0.5) / parent_tex_size * 2.0;

    // Filter the image, see:
    // http://fs5.directupload.net/images/151213/qfnexcls.png
    vec3 center_sample = textureLod(SourceTex, flt_coord, SourceMip).xyz;

    // inner samples (marked red)
    vec3 sample_r_tl = textureLod(SourceTex, flt_coord + vec2(-1, 1 ) * texel_size, SourceMip).xyz;
    vec3 sample_r_tr = textureLod(SourceTex, flt_coord + vec2( 1, 1 ) * texel_size, SourceMip).xyz;
    vec3 sample_r_bl = textureLod(SourceTex, flt_coord + vec2(-1,-1 ) * texel_size, SourceMip).xyz;
    vec3 sample_r_br = textureLod(SourceTex, flt_coord + vec2( 1,-1 ) * texel_size, SourceMip).xyz;

    // corner samples
    vec3 sample_t = textureLod(SourceTex, flt_coord + vec2( 0, 2 ) * texel_size, SourceMip).xyz;
    vec3 sample_r = textureLod(SourceTex, flt_coord + vec2( 2, 0 ) * texel_size, SourceMip).xyz;
    vec3 sample_b = textureLod(SourceTex, flt_coord + vec2( 0,-2 ) * texel_size, SourceMip).xyz;
    vec3 sample_l = textureLod(SourceTex, flt_coord + vec2(-2, 0 ) * texel_size, SourceMip).xyz;

    // edge samples
    vec3 sample_tl = textureLod(SourceTex, flt_coord + vec2( -2, 2 ) * texel_size, SourceMip).xyz;
    vec3 sample_tr = textureLod(SourceTex, flt_coord + vec2(  2, 2 ) * texel_size, SourceMip).xyz;
    vec3 sample_bl = textureLod(SourceTex, flt_coord + vec2( -2,-2 ) * texel_size, SourceMip).xyz;
    vec3 sample_br = textureLod(SourceTex, flt_coord + vec2(  2,-2 ) * texel_size, SourceMip).xyz;

    vec3 kernel_sum_red    = sample_r_tl + sample_r_tr + sample_r_bl + sample_r_br;
    vec3 kernel_sum_yellow = sample_tl + sample_t + sample_l + center_sample;
    vec3 kernel_sum_green  = sample_tr + sample_t + sample_r + center_sample;
    vec3 kernel_sum_purple = sample_bl + sample_b + sample_l + center_sample;
    vec3 kernel_sum_blue   = sample_br + sample_b + sample_r + center_sample;

    vec3 summed_kernel = kernel_sum_red * 0.5 + 
                         kernel_sum_yellow * 0.125 + 
                         kernel_sum_green  * 0.125 +
                         kernel_sum_purple * 0.125 +
                         kernel_sum_blue   * 0.125;

    // since every sub-kernel has 4 samples, normalize that
    summed_kernel /= 4.0;

    // FIX: AMD drivers optimize out texcoord if we don't use it. So just assign
    // it to a non-meaningful variable
    float AMD_DRIVER_FIX = texcoord.x * 1e-28;

    // result = vec4(summed_kernel, 1.0);
    imageStore(DestTex, ivec2(gl_FragCoord.xy), vec4(summed_kernel, AMD_DRIVER_FIX));
}

