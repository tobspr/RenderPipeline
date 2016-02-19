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

#version 400

#pragma include "render_pipeline_base.inc.glsl"
#pragma include "includes/color_spaces.inc.glsl"

uniform sampler2D ShadedScene;
out vec4 result;

void main() {

    vec2 texcoord = get_texcoord();
    vec3 scene_color = textureLod(ShadedScene, texcoord, 0).xyz;

    // Compute the sharpen strength for each individual channel
    float sharpen_strength = GET_SETTING(color_correction, sharpen_strength);
    vec3 sharpen_luma_strength = LUMA_COEFFS * sharpen_strength;

    vec2 pixel_size = 1.0 / SCREEN_SIZE;

    // Blur arround the current pixel
    vec3 blur_sum = vec3(0);

    // 2 samples
    #if 0
        blur_sum += textureLod(ShadedScene, texcoord + pixel_size / 3.0, 0).xyz;
        blur_sum += textureLod(ShadedScene, texcoord - pixel_size / 3.0, 0).xyz;
        sharpen_luma_strength *= 1.5;
        blur_sum *= 1.0 / 2.0;
    #endif

    // 4 samples
    #if 1
        blur_sum += textureLod(ShadedScene, texcoord + vec2(  0.5, -0.5 ) * pixel_size, 0).rgb;
        blur_sum += textureLod(ShadedScene, texcoord + vec2( -0.5, -0.5 ) * pixel_size, 0).rgb;
        blur_sum += textureLod(ShadedScene, texcoord + vec2(  0.5, 0.5  ) * pixel_size, 0).rgb;
        blur_sum += textureLod(ShadedScene, texcoord + vec2( -0.5, 0.5  ) * pixel_size, 0).rgb;
        blur_sum *= 1.0 / 4.0;
    #endif

    vec3 pixel_diff = scene_color - blur_sum;

    // Apply the sharpening
    scene_color += dot(pixel_diff, sharpen_luma_strength);

    result = vec4(scene_color, 1.0);
}
