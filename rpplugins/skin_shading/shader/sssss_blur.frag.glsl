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

#version 420

#define USE_MAIN_SCENE_DATA
#define USE_GBUFFER_EXTENSIONS
#pragma include "render_pipeline_base.inc.glsl"
#pragma include "includes/gbuffer.inc.glsl"

#pragma include "SeperableSSS.inc.glsl"

uniform sampler2D SourceTex;
uniform ivec2 direction;

out vec3 color;

void main() {
  vec2 texcoord = get_texcoord();
  int shading_model = get_gbuffer_shading_model(GBuffer, texcoord);
  const float sssWidth = 0.002 * GET_SETTING(skin_shading, blur_scale);
  float sssScale = shading_model == SHADING_MODEL_SKIN ? 1.0 : 0.0;
  vec4 blur_result = SSSSBlurPS(texcoord, SourceTex, GBuffer.Depth, sssWidth, sssScale, direction);
  color = blur_result.xyz;

  #if DEBUG_MODE
    color = texture(SourceTex, texcoord).xyz;
  #endif
}
