#version 430

// Precomputes the film grain

layout (local_size_x = 16, local_size_y = 16, local_size_z = 1) in;

#define SCREEN_SIZE vec2(1024, 1024)
#pragma include "../../rpcore/shader/includes/noise.inc.glsl"

uniform writeonly image2D DestTex;

float grain_rand(vec2 co){
    return fract(sin(dot(co.xy ,vec2(12.9898,78.233))) * 43758.5453);
}

float generate_grain(vec2 texCoord, float frame) {
  vec2 resolution = vec2(1920, 1080);
  vec2 mult = texCoord * resolution;
  float initial_offset = grain_rand(texCoord);
  float offset = snoise3D(vec3(texCoord.yx * resolution + texCoord.x * 1112.0 + texCoord.y * 1891.0 + initial_offset * 2000.0, mod(frame,300.0) ))*0.5 + 0.5;
  float n1 = offset;
  return n1 * 0.5 + 0.5;
}

void main() {
  vec2 texcoord = vec2(ivec2(gl_GlobalInvocationID.xy) + 0.5) / 1024.0;
  vec4 result = vec4(0);
  result.x = generate_grain(texcoord, 50.0);
  result.y = generate_grain(texcoord, 100.0);
  result.z = generate_grain(texcoord, 150.0);
  result.w = generate_grain(texcoord, 200.0);
  imageStore(DestTex, ivec2(gl_GlobalInvocationID.xy), result);
}
