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

uniform sampler2D DefaultSkydome;
uniform sampler2D DefaultSkydomeOverlay;


// Computes the skydome texcoord based on the pixels view direction
vec2 get_skydome_coord(vec3 view_dir) {
    float angle = (atan(view_dir.x, view_dir.y) + M_PI) / (2.0 * M_PI);
    // angle += MainSceneData.frame_time * 0.001074564;
    angle += 0.4;
    angle = mod(angle + 10, 1.0); // +10 to avoid negative numbers, since this is UB

    view_dir.z *= 0.5;
    view_dir.z += 0.5;
    return vec2(angle, view_dir.z);
}


// Computes the skydome texcoord based on the pixels view direction
vec2 get_overlay_coord(vec3 view_dir) {
    float angle = (atan(view_dir.x, view_dir.y) + M_PI) / (2.0 * M_PI);
    angle += MainSceneData.frame_time * 0.0031723;
    angle = mod(angle + 10, 1.0); // +10 to avoid negative numbers, since this is UB

    // view_dir.z += 1.0;
    // view_dir.z *= 0.5;
    return vec2(angle, view_dir.z);
}

vec3 get_merged_scattering(vec3 view_vector, vec3 inscattered_light)
{

  // Render clouds to provide more variance for the cubemap
  vec2 skydome_coord = get_skydome_coord(view_vector);
  
  vec3 cloud_color = textureLod(DefaultSkydome, skydome_coord, 0).xyz;
  cloud_color *= cloud_color * 7;
  cloud_color = mix(vec3(0.5), cloud_color, saturate((view_vector.z + 0.01) / 0.25));
  // cloud_color = mix(vec3(0.5), cloud_color, saturate((0.9 - view_vector.z) / 0.3));

  // inscattered_light *= 2 * cloud_color * vec3(1, 0.7, 0.5);

  // inscattered_light *= 10;

  // Add another layer which moves into the opposite direction
  vec2 overlay_coord = get_overlay_coord(view_vector);
  vec3 overlay_color = textureLod(DefaultSkydomeOverlay, overlay_coord, 0).xyz;
  // overlay_color = mix(vec3(2, 1.5, 1), overlay_color, satura(te((view_vector.z + 0.1) / 0.3));

  // inscattered_light *= vec3(0.3) + overlay_color * 6 * vec3(1.0, 0.5, 0.4);
  // inscattered_light *= 0.4;

  return inscattered_light;
//   return cloud_color * 10.0;
}
