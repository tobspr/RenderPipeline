#version 400

#pragma include "Includes/Configuration.inc.glsl"
#pragma include "Includes/ColorSpaces/ColorSpaces.inc.glsl"

uniform sampler2D SourceTex;
out vec4 result;

void main() {

    vec2 texcoord = get_texcoord();

    vec3 scene_color = textureLod(SourceTex, texcoord, 0).xyz;

    // Compute the sharpen strength for each individual channel
    float sharpen_strength = GET_SETTING(ColorCorrection, sharpen_strength);
    vec3 sharpen_luma_strength = LUMA_COEFFS * sharpen_strength;

    vec2 pixel_size = 1.0 / SCREEN_SIZE;


    // Blur arround the current pixel
    vec3 blur_sum = vec3(0);

    // 2 samples
    #if 0
        // blur_sum += textureLod(SourceTex, texcoord + pixel_size / 3.0, 0).xyz;
        // blur_sum += textureLod(SourceTex, texcoord - pixel_size / 3.0, 0).xyz;
        sharpen_luma_strength *= 1.5;
        blur_sum *= 1.0 / 2.0;
    #endif

    // 4 samples
    #if 1
        blur_sum += textureLod(SourceTex, texcoord + vec2(  0.4, -1.2 ) * pixel_size, 0).rgb;
        blur_sum += textureLod(SourceTex, texcoord + vec2( -1.2, -0.4 ) * pixel_size, 0).rgb;
        blur_sum += textureLod(SourceTex, texcoord + vec2(  1.2, 0.4  ) * pixel_size, 0).rgb;
        blur_sum += textureLod(SourceTex, texcoord + vec2( -0.4, 1.2  ) * pixel_size, 0).rgb;
        blur_sum *= 1.0 / 4.0;
    #endif

    vec3 pixel_diff = scene_color - blur_sum;

    // Make sure we don't sharpen too much
    float luma_sharpen = dot(pixel_diff, sharpen_luma_strength);
    // float max_sharpen = 0.1;
    // luma_sharpen = clamp(luma_sharpen, -max_sharpen, max_sharpen);

    // Apply the sharpening
    scene_color += luma_sharpen;

    result = vec4(scene_color, 1.0);
}
