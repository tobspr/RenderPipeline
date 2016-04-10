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



// Halton sequences

CONST_ARRAY vec2[] halton_32 = vec2[32](
  vec2(0, -0.166667),
  vec2(-0.25, 0.166667),
  vec2(0.25, -0.388889),
  vec2(-0.375, -0.0555556),
  vec2(0.125, 0.277778),
  vec2(-0.125, -0.277778),
  vec2(0.375, 0.0555556),
  vec2(-0.4375, 0.388889),
  vec2(0.0625, -0.462963),
  vec2(-0.1875, -0.12963),
  vec2(0.3125, 0.203704),
  vec2(-0.3125, -0.351852),
  vec2(0.1875, -0.0185185),
  vec2(-0.0625, 0.314815),
  vec2(0.4375, -0.240741),
  vec2(-0.46875, 0.0925926),
  vec2(0.03125, 0.425926),
  vec2(-0.21875, -0.425926),
  vec2(0.28125, -0.0925926),
  vec2(-0.34375, 0.240741),
  vec2(0.15625, -0.314815),
  vec2(-0.09375, 0.0185185),
  vec2(0.40625, 0.351852),
  vec2(-0.40625, -0.203704),
  vec2(0.09375, 0.12963),
  vec2(-0.15625, 0.462963),
  vec2(0.34375, -0.487654),
  vec2(-0.28125, -0.154321),
  vec2(0.21875, 0.179012),
  vec2(-0.03125, -0.376543),
  vec2(0.46875, -0.0432099),
  vec2(-0.484375, 0.290123)
);
