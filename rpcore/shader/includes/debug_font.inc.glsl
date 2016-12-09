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


#pragma once

// Utility methods to render text in a shader

uniform sampler2D DebugFontAtlas;
const int digit_width = 5;
const int digit_height = 8;
const int spacing = 1;

int get_digit_count(uint number) {
    return int(log(float(number)) / log(10.0) + 1e-6) + 1;
}

float render_digit(ivec2 coord, uint digit) {
    ivec2 offset = ivec2(digit * digit_width, 0);
    ivec2 pointer = ivec2(gl_FragCoord.xy);
    ivec2 sample_coord = pointer - coord;
    if (sample_coord.x < 0 || sample_coord.y < 0 || sample_coord.x >= digit_width || sample_coord.y >= digit_height) {
        return 0.0;
    }
    return 1 - texelFetch(DebugFontAtlas, sample_coord + offset, 0).x;
}

float render_number(ivec2 coord, uint number) {
    int num_digits = max(1, get_digit_count(number));
    float accum = 0.0;
    for (int i = num_digits - 1; i >= 0; --i) {
        accum += render_digit(coord + ivec2(i * (spacing + digit_width), 0), number % 10);
        number /= 10;
    }
    return accum;
}
