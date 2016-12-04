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

#version 430

// This shader applies the ambient term to the shaded scene

#pragma include "render_pipeline_base.inc.glsl"
#pragma include "includes/color_spaces.inc.glsl"
#pragma include "includes/noise.inc.glsl"

uniform sampler2D ShadedScene;
out vec3 result;

void main() {
    vec2 texcoord = get_texcoord();
    vec3 scene_color = textureLod(ShadedScene, texcoord, 0).xyz;

    #if !DEBUG_MODE
        scene_color = rgb_to_srgb(scene_color);
        scene_color = saturate(scene_color);

        // Apply dithering to prevent banding, since we are converting from 16 bit
        // precision to 8 bit precision here
        vec3 dither = (rand_rgb(texcoord) + rand_rgb(texcoord + 0.5787)) * 0.5 - 0.4;
        scene_color += dither / 255.0;
    #endif


    #if SPECIAL_MODE_ACTIVE(LUMINANCE)

        // Luminance debug mode, too bright pixels get red, too dark pixels get blue,
        // rest stays green
        float luminance = get_luminance(scene_color);

        vec3 color_ok = vec3(0, 1, 0);
        vec3 color_too_bright = vec3(1, 0, 0);
        vec3 color_too_dark = vec3(0, 0, 1);

        const float max_brightness = 0.7;
        const float max_darkness = 0.3;

        scene_color = mix(color_ok, color_too_bright, saturate(5.0 * (luminance - max_brightness)));
        scene_color = mix(scene_color, color_too_dark, saturate(5.0 * (max_darkness - luminance)));

    #endif


    result = scene_color;
}
