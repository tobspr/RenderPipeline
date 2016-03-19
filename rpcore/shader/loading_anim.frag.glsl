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

in vec2 texcoord;
uniform sampler2D p3d_Texture0;
out vec4 result;
uniform int frameIndex;

void main() {
  vec2 texsize = textureSize(p3d_Texture0, 0).xy;
  float offs_x = float(int(frameIndex % 12)) * 420.0 / texsize.x;
  float offs_y = float(11 - int(frameIndex / 12)) * 420.0 / texsize.y;
  vec2 tcoord = texcoord / 12.0 + vec2(offs_x, offs_y);

  vec2 data = texture(p3d_Texture0, tcoord).xw;
  data.x = (1 - data.x) * 0.917;
  result = data.xxxy;
}
