#version 400

#pragma optionNV (unroll all)

#pragma include "Includes/Configuration.inc.glsl"
#pragma include "Includes/GBuffer.inc.glsl"
#pragma include "Includes/PositionReconstruction.inc.glsl"

uniform ivec2 blur_direction;
uniform sampler2D SourceTex;
uniform GBufferData GBuffer;

out vec4 result;


float get_lin_z(ivec2 ccoord) {
    return getLinearZFromZ(get_gbuffer_depth(GBuffer, ccoord));
}

void do_blur(ivec2 coord, int i, float weight, vec3 pixel_nrm, float pixel_depth, inout vec4 accum, inout float accum_w) {

    // Notice: We can advance 2 pixels at once, since
    // we did a bilateral upscale. So only every second pixel
    // contains new information
    ivec2 offcord = coord + i * blur_direction * 1;
    vec4 sampled = texelFetch(SourceTex, offcord, 0);
    vec3 nrm = get_gbuffer_normal(GBuffer, offcord);
    float d = get_lin_z(offcord);

    weight *= 1.0 - saturate(GET_SETTING(AO, blur_normal_factor) * distance(nrm, pixel_nrm));
    weight *= 1.0 - saturate(GET_SETTING(AO, blur_depth_factor) * abs(d - pixel_depth));

    accum += sampled * weight;
    accum_w += weight;

}


void main() {

    ivec2 coord = ivec2(gl_FragCoord.xy);

    vec4 accum = vec4(0);
    float accum_w = 0.0;

    const int blur_size = 9;

    float weights[blur_size] = float[blur_size](
        0.132980,
        0.125858,
        0.106701,
        0.081029,
        0.055119,
        0.033585,
        0.018331,
        0.008962,
        0.003924
    );

    vec3 pixel_nrm = get_gbuffer_normal(GBuffer, coord);
    float pixel_depth = get_lin_z(coord);

    for (int i = 0; i < blur_size; ++i) {
        float weight = weights[i];
        do_blur(coord, i, weight, pixel_nrm, pixel_depth, accum, accum_w);
    }

    for (int i = -1; i > -blur_size; --i) {
        float weight = weights[-i];
        do_blur(coord, i, weight, pixel_nrm, pixel_depth, accum, accum_w);
    }

    accum /= max(0.01, accum_w);
    result = accum;

}