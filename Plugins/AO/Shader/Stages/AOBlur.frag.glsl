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

float get_lin_z(vec2 ccoord) {
    return get_linear_z_from_z(get_gbuffer_depth(GBuffer, ccoord));
}

const vec2 pixel_size = 2.0 / SCREEN_SIZE;

void do_blur(vec2 coord, int i, float weight, vec3 pixel_nrm, float pixel_depth, inout vec4 accum, inout float accum_w) {

    vec2 offcoord = coord + pixel_size * i * blur_direction;
    vec4 sampled = textureLod(SourceTex, offcoord, 0);
    vec3 nrm = get_gbuffer_normal(GBuffer, offcoord);
    float d = get_lin_z(offcoord);

    weight *= 1.0 - saturate(GET_SETTING(AO, blur_normal_factor) * distance(nrm, pixel_nrm));
    weight *= 1.0 - saturate(GET_SETTING(AO, blur_depth_factor) * abs(d - pixel_depth));

    accum += sampled * weight;
    accum_w += weight;
}


void main() {

    vec2 texcoord = get_half_native_texcoord();

    // Store accumulated color
    vec4 accum = vec4(0);
    float accum_w = 0.0;

    // Get the weights array
    const int blur_size = 5;
    CONST_ARRAY float weights[blur_size] = gaussian_weights_5; // <-- this is based on the blur size

    // Get the mid pixel normal and depth
    vec3 pixel_nrm = get_gbuffer_normal(GBuffer, texcoord);
    float pixel_depth = get_lin_z(texcoord);

    // Blur to the right
    for (int i = 0; i < blur_size; ++i) {
        float weight = weights[i];
        do_blur(texcoord, i, weight, pixel_nrm, pixel_depth, accum, accum_w);
    }

    // Blur to the left
    for (int i = -1; i > -blur_size; --i) {
        float weight = weights[-i];
        do_blur(texcoord, i, weight, pixel_nrm, pixel_depth, accum, accum_w);
    }

    accum /= max(0.01, accum_w);
    result = accum;
}
