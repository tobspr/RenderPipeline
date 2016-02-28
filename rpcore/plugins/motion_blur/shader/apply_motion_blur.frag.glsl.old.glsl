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
#pragma include "includes/noise.inc.glsl"

uniform sampler2D ShadedScene;
uniform sampler2D NeighborMinMax;

out vec3 result;

// Based on:
// http://graphics.cs.williams.edu/papers/MotionBlurI3D12/McGuire12Blur.pdf

float cone(float dist, float r) {
    return saturate(1.0 - abs(dist) / r);
}


float cylinder(float dist, float r) {
    return 1.0 - smoothstep(r * 0.95, r * 1.05, abs(dist));

    // Alternative: (marginally faster on GeForce, comparable quality)
    // return sign(r - abs(dist)) * 0.5 + 0.5;

    // The following gives nearly identical results and may be faster on some hardware,
    // but is slower on GeForce
    //    return (abs(dist) <= r) ? 1.0 : 0.0;
}

/** 0 if depth_A << depth_B, 1 if depth_A >> z_depth, fades between when they are close */
float soft_depth_cmp(float depth_A, float depth_B) {
    // World space distance over which we are conservative about the classification
    // of "foreground" vs. "background".  Must be > 0.
    // Increase if slanted surfaces aren't blurring enough.
    // Decrease if the background is bleeding into the foreground.
    // Fairly insensitive
    const float SOFT_DEPTH_EXTENT = 0.09;

    return saturate(1.0 - (depth_B - depth_A) / SOFT_DEPTH_EXTENT);
}

const int tile_size = 20;
// const float exposure_time = 60.0 / 1000.0;
const float exposure_time = 2.0;

vec2 transform_velocity(vec2 velocity, out float r) {
  float len = length(velocity);
  r = clamp(len * 0.5 * exposure_time, 0.5, float(tile_size));
  if (r >= 0.01) {
    velocity *= r / len;
  }
  return velocity;
}


vec2 DepthCmp(  float centerDepth,
    float sampleDepth,
    float depthScale )
{
return saturate( 0.5 + vec2( depthScale, -depthScale ) *
  ( sampleDepth - centerDepth ));
}

vec2 SpreadCmp(float offsetLen, vec2 spreadLen, float pixelToSampleUnitsScale)
{
  return saturate( pixelToSampleUnitsScale * spreadLen - offsetLen + 1.0 );
}

float SampleWeight( float centerDepth, float sampleDepth, float offsetLen, float centerSpreadLen,
    float sampleSpreadLen, float pixelToSampleUnitsScale, float depthScale )
{
vec2 depthCmp = DepthCmp( centerDepth, sampleDepth, depthScale );
vec2 spreadCmp = SpreadCmp( offsetLen, vec2( centerSpreadLen, sampleSpreadLen ), pixelToSampleUnitsScale );
return dot( depthCmp, spreadCmp );
}



void main() {

  ivec2 coord = ivec2(gl_FragCoord.xy);
  ivec2 tile = coord / tile_size;

  vec3 center_color = texelFetch(ShadedScene, coord, 0).xyz;

  float tile_velocity_len;
  vec2 tile_velocity = transform_velocity(texelFetch(NeighborMinMax, tile, 0).xy, tile_velocity_len);

  if (tile_velocity_len < 0.505) {
    result = center_color;
    return;
  }

  float center_depth = get_depth_at(coord); // = Z[X]
  float center_radius;
  vec2 center_velocity = transform_velocity(get_velocity_at(coord), center_radius); // = V[X]

  float jitter = rand(vec2(coord)) * 1;
  const int num_samples = 32;


  // float weights = float(num_samples) / (100.0 * center_radius);
  // vec3 sum = center_color * weights;

  // weights = 0.0;
  // sum *= 0;
  vec4 sum = vec4(0);

  for (int i = 0; i <= num_samples; ++i) {
    if (i == num_samples / 2) continue;
    float t = mix(-1.0, 1.0, (i + jitter + 1.0) / (num_samples + 1.0));
    // float t = clamp(2.4 * (float(i) + 1.0 + jitter) / (numSamplesOdd + 1.0) - 1.2, -1, 1);

    ivec2 sample_coord = ivec2(coord + tile_velocity * t + 0.5);
    float sample_depth = get_depth_at(sample_coord); // = Z[Y]
    float sample_radius;
    vec2 sample_velocity = transform_velocity(get_velocity_at(sample_coord), sample_radius); // = V[Y]

    float dist = t * tile_velocity_len;
    float pixelToSampleUnitsScale = 0.5;

    float weight = SampleWeight(center_depth, sample_depth, dist, center_radius,
          sample_radius, pixelToSampleUnitsScale, 20000.0);

    // float fg = soft_depth_cmp(center_depth, sample_depth);
    // float bg = soft_depth_cmp(sample_depth, center_depth);


    // float weight = fg * cone(dist, sample_radius);
    // weight += bg * cone(dist, center_radius);
    // weight += cylinder(dist, min(sample_radius, center_radius) ) * 2.0;

    // weights += weight;
    sum += vec4(texelFetch(ShadedScene, sample_coord, 0).xyz, 1) * weight;
  }

  sum /= num_samples;
  // sum /= max(1e-5, weights);
  result = sum.rgb + (1.0 - sum.w) * center_color;

}
