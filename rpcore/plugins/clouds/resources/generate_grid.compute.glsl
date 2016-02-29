#version 430

// Shader to generate the cloud grid

#define SCREEN_SIZE vec2(32, 32)

#pragma include "../../../shader/includes/noise.inc.glsl"

layout (local_size_x = 8, local_size_y = 8, local_size_z = 4) in;

uniform writeonly image3D DestTex;

void main() {

  ivec3 coord = ivec3(gl_GlobalInvocationID.xyz);


  vec3 flt_coord = coord;

  float factor = snoise3D(flt_coord * 0.01) * 0.5 + 0.5;

  imageStore(DestTex, coord, vec4(1, 1, 1, factor));

}
