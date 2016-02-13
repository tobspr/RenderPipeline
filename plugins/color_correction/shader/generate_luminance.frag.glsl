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


float get_log_luminance(vec3 color) {
    float lum = get_luminance(color);
    lum = lum / (1 + lum);
    return max(0.0, lum);
}

void main() {

    ivec2 coord_screen = ivec2(gl_FragCoord.xy) * 4;
    vec2 local_coord = (coord_screen+1.0) / SCREEN_SIZE;
    vec2 pixel_offset = 2.0 / SCREEN_SIZE;

    float lum0 = get_log_luminance(textureLod(ShadedScene, local_coord, 0).xyz);
    float lum1 = get_log_luminance(textureLod(ShadedScene, local_coord + vec2(pixel_offset.x, 0), 0).xyz);
    float lum2 = get_log_luminance(textureLod(ShadedScene, local_coord + vec2(0, pixel_offset.y), 0).xyz);
    float lum3 = get_log_luminance(textureLod(ShadedScene, local_coord + pixel_offset.xy, 0).xyz);

    result = vec4( (lum0 + lum1 + lum2 + lum3) * 0.25 );
}
