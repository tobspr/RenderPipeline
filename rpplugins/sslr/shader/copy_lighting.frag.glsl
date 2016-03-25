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

#pragma include "render_pipeline_base.inc.glsl"

uniform sampler2D CombinedVelocity;
uniform writeonly image2D RESTRICT DestTex;
uniform sampler2D Previous_PostAmbientScene;

void main() {
  vec2 texcoord = get_texcoord();
  vec2 velocity = texture(CombinedVelocity, texcoord).xy;
  vec2 last_coord = texcoord + velocity;

  // Out of screen, can early out
  if (out_of_screen(last_coord)) {
    imageStore(DestTex, ivec2(gl_FragCoord.xy), vec4(0));
    return;
  }

  float border_fade = 0.05;

  float fade = 1.0;
  fade *= saturate(last_coord.x / border_fade) * saturate(last_coord.y / border_fade);
  fade *= saturate((1-last_coord.x) / border_fade) * saturate((1-last_coord.y) / border_fade);

  // TODO: Compute a weight based on the normal and depth/difference and so on
  // TODO: Fade at screen borders

  vec3 intersected_color = texture(Previous_PostAmbientScene, last_coord).xyz;
  intersected_color = clamp(intersected_color, vec3(0), vec3(100));

  // result = vec4(intersected_color, 1) * fade;
  imageStore(DestTex, ivec2(gl_FragCoord.xy), vec4(intersected_color, 1) * fade);
}
