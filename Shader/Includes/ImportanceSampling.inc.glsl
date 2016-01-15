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

#pragma once

#pragma include "Includes/Configuration.inc.glsl"

// From:
// http://blog.tobias-franke.eu/2014/03/30/notes_on_importance_sampling.html
vec2 importance_sample_ggx(vec2 xi, float roughness)
{
  float phi = TWO_PI * xi.x;
  float theta = acos(sqrt((1.0 - xi.y) / ((roughness * roughness - 1.0) * xi.y + 1.0)));
  return vec2(phi, theta);
}

// From:
// http://www.trentreed.net/blog/physically-based-shading-and-image-based-lighting/
vec2 hammersley(uint i, uint N)
{
  return vec2(float(i) / float(N), float(bitfieldReverse(i)) * 2.3283064365386963e-10);
} 

// From:
// http://www.gamedev.net/topic/655431-ibl-problem-with-consistency-using-ggx-anisotropy/
vec3 ImportanceSampleGGX(vec2 Xi, float roughness, vec3 n)
{
  float r_square = roughness * roughness;
  float phi = TWO_PI * Xi.x;
  float cos_theta = sqrt((1 - Xi.y) / (1 + (r_square*r_square - 1) * Xi.y));   
  float sin_theta = sqrt(1 - cos_theta * cos_theta);

  vec3 h = vec3(sin_theta * cos(phi), sin_theta * sin(phi), cos_theta);
  vec3 up_vector = abs(n.z) < 0.999 ? vec3(0, 0, 1) : vec3(1, 0, 0);
  vec3 tangent = normalize(cross(up_vector, n));
  vec3 bitangent = normalize(cross(n, tangent));

  // Tangent to world space
  return normalize(tangent * h.x + bitangent * h.y + n * h.z);
}

vec3 ImportanceSampleLambert(vec2 xi, vec3 n)
{
  float phi = TWO_PI * xi.x;
  float cos_theta = sqrt(1 - xi.y);
  float sin_theta = sqrt(1 - cos_theta * cos_theta);

  vec3 h = vec3(sin_theta * cos(phi), sin_theta * sin(phi), cos_theta);

  // Find arbitrary tangent
  vec3 up_vector = abs(n.z) < 0.999 ? vec3(0, 0, 1) : vec3(1, 0, 0);
  vec3 tangent = normalize(cross(up_vector, n));
  vec3 bitangent = normalize(cross(n, tangent));

  // Tangent to world space
  return normalize(tangent * h.x + bitangent * h.y + n * h.z);
}

