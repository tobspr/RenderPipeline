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


#define USE_MAIN_SCENE_DATA
#define USE_GBUFFER_EXTENSIONS
#pragma include "render_pipeline_base.inc.glsl"
#pragma include "includes/gbuffer.inc.glsl"

uniform sampler2D MipChain;
uniform sampler2D TraceResult;
out vec4 result;

// Based on
// http://roar11.com/2015/07/screen-space-glossy-reflections/

// Phong - TODO: Convert to GGX
float specular_power_to_cone_angle(float specular_power)
{
 if(specular_power >= 4096)
  return 0.0;
 const float xi = 0.244;
 float exponent = 1.0 / (specular_power + 1);
 return acos(pow(xi, exponent));
}

float isosceles_triangle_opposite(float adjacent_length, float cone_theta)
{
 return 2.0 * tan(cone_theta) * adjacent_length;
}

float isosceles_triangle_in_radius(float a, float h)
{
 float a2 = a * a;
 float fh2 = 4.0 * h * h;
 return (a * (sqrt(a2 + fh2) - a)) / (4.0 * h);
}

float roughness_to_specular_power(float roughness) {
  return pow(2.0, (1.0 - roughness) * 10.0 + 2.0);
}

void main() {

  vec2 texcoord = get_half_texcoord();
  vec3 trace_data = textureLod(TraceResult, texcoord, 0).xyz;

  Material m = unpack_material(GBuffer, texcoord);

  const int num_steps = 5;

  // Skip pixels with no reflection data
  if (trace_data.z <= 0.0) {
    result = vec4(0);
    return;
  }

  float roughness = m.shading_model == SHADING_MODEL_CLEARCOAT ? CLEARCOAT_ROUGHNESS : sqrt(m.roughness);
  const float max_mip_level = 8; // Could make this dynamic, but no need for it
  vec2 trace_end = trace_data.xy;
  float gloss = 1 - roughness;

  // Find the cone parameters
  float specular_power = roughness_to_specular_power(roughness);
  float cone_theta = specular_power_to_cone_angle(specular_power) * 0.5;
  float adjacent_length = distance(texcoord, trace_end);
  vec2 adjacent_unit = normalize(trace_end - texcoord);

  float gloss_mult = gloss;
  vec4 accum = vec4(0);

  // Trace alongs the cone
  for (int i = 0; i < num_steps; ++i) {
    float opposide_length = isosceles_triangle_opposite(adjacent_length, cone_theta);
    float incircle_size = isosceles_triangle_in_radius(opposide_length, adjacent_length);
    vec2 sample_pos = texcoord + adjacent_unit * (adjacent_length - incircle_size);
    float mip_channel = clamp(log2(incircle_size * WINDOW_WIDTH), 0.0, max_mip_level);
    vec4 color_sample = textureLod(MipChain, sample_pos, mip_channel) * gloss_mult;

    // Accumulate the color based on the remaining weight - the colors weight
    // is already premultiplied
    accum += color_sample * (1 - accum.w);
    adjacent_length -= 2.0 * incircle_size;
    gloss_mult *= gloss;
  }

  // Also apply fading factors from the trace passv
  result = accum * trace_data.z;
}
