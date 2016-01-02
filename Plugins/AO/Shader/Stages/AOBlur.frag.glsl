#version 420

#pragma optionNV (unroll all)

#define USE_MAIN_SCENE_DATA
#pragma include "Includes/Configuration.inc.glsl"
#pragma include "Includes/GBuffer.inc.glsl"
#pragma include "Includes/PositionReconstruction.inc.glsl"
#pragma include "Includes/GaussianWeights.inc.glsl"

uniform ivec2 blur_direction;
uniform sampler2D SourceTex;
uniform GBufferData GBuffer;

out vec4 result;


float get_lin_z(ivec2 ccoord) {
    return get_linear_z_from_z(get_gbuffer_depth(GBuffer, ccoord));
}

void do_blur(ivec2 coord, int i, float weight, vec3 pixel_nrm, float pixel_depth, inout vec4 accum, inout float accum_w) {

    // Notice: We can advance 2 pixels at once, since
    // we did a bilateral upscale. So only every second pixel
    // contains new information
    ivec2 offcord = coord + i * blur_direction;
    vec4 sampled = texelFetch(SourceTex, offcord, 0);
    vec3 nrm = get_gbuffer_normal(GBuffer, offcord * 2);
    float d = get_lin_z(offcord * 2);

    weight *= 1.0 - saturate(GET_SETTING(AO, blur_normal_factor) * distance(nrm, pixel_nrm));
    weight *= 1.0 - saturate(GET_SETTING(AO, blur_depth_factor) * abs(d - pixel_depth));

    accum += sampled * weight;
    accum_w += weight;
}


void main() {
    ivec2 coord = ivec2(gl_FragCoord.xy);
    
    // Store accumulated color
    vec4 accum = vec4(0);
    float accum_w = 0.0;

    // Get the weights array
    const int blur_size = 5;
    const float weights[blur_size] = gaussian_weights_5; // <-- this is based on the blur size

    // Get the mid pixel normal and depth
    vec3 pixel_nrm = get_gbuffer_normal(GBuffer, coord * 2);
    float pixel_depth = get_lin_z(coord * 2);

    // Blur to the right
    for (int i = 0; i < blur_size; ++i) {
        float weight = weights[i];
        do_blur(coord, i, weight, pixel_nrm, pixel_depth, accum, accum_w);
    }

    // Blur to the left
    for (int i = -1; i > -blur_size; --i) {
        float weight = weights[-i];
        do_blur(coord, i, weight, pixel_nrm, pixel_depth, accum, accum_w);
    }

    accum /= max(0.01, accum_w);
    result = accum;

}