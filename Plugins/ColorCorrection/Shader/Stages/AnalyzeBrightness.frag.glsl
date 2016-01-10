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

#version 440

#define USE_MAIN_SCENE_DATA
#define USE_TIME_OF_DAY
#pragma include "Includes/Configuration.inc.glsl"

uniform layout(rgba16f) imageBuffer RESTRICT ExposureStorage;
uniform sampler2D DownscaledTex;

void main() {

    // Manually do the last downscale step
    ivec2 texsize = textureSize(DownscaledTex, 0).xy;
    float avg_luminance = 0.0;
    for (int x = 0; x < texsize.x; ++x) {
        for (int y = 0; y < texsize.y; ++y) {
            avg_luminance += texelFetch(DownscaledTex, ivec2(x, y), 0).x;
        }
    }

    avg_luminance /= float(texsize.x * texsize.y);
    avg_luminance = avg_luminance / (1 - avg_luminance);
    avg_luminance *= GET_SETTING(ColorCorrection, brightness_scale);


    const float factor = 12.0;
    float min_exp = make_logarithmic(GET_SETTING(ColorCorrection, min_exposure), factor);
    float max_exp = make_logarithmic(GET_SETTING(ColorCorrection, max_exposure), factor);
    float exp_bias = GET_SETTING(ColorCorrection, exposure_bias) * 10.0;

    avg_luminance = max(min_exp, min(max_exp, 0.2 / (avg_luminance) + exp_bias));

    // Transition between the last and current value smoothly
    float cur_luminance = imageLoad(ExposureStorage, 0).x;
    float adaption_rate = GET_SETTING(ColorCorrection, brightness_adaption_rate);

    if (cur_luminance < avg_luminance) {
        adaption_rate = GET_SETTING(ColorCorrection, darkness_adaption_rate);
    }

    float adjustment = saturate(MainSceneData.frame_delta * adaption_rate);
    float new_luminance = mix(cur_luminance, avg_luminance, adjustment);
    imageStore(ExposureStorage, 0, vec4(new_luminance));
}
