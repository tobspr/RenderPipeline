#version 430

// Shader to generate the cloud grid

#define SCREEN_SIZE vec2(32, 32)

#pragma include "../../../rpcore/shader/includes/noise.inc.glsl"

layout (local_size_x = 8, local_size_y = 8, local_size_z = 4) in;

uniform writeonly image3D DestTex;



void main() {

  ivec3 coord = ivec3(gl_GlobalInvocationID.xyz);


  vec3 flt_coord = coord;

  float factor = fbm(flt_coord / vec3(512.0, 512, 2.0 * 512.0) , 8.0);

  factor = (factor - 0.5) * 4.5;

  factor = clamp(factor, 0.0, 1.0);
  vec3 color = vec3(0.05 + pow(coord.z / 64.0, 2.0) );
  color = clamp(color, vec3(0.0), vec3(1.0));
  // color *= factor;

  imageStore(DestTex, coord, vec4(factor, color.x, 0, 1));

}
