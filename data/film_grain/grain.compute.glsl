#version 430

// Precomputes the film grain

layout (local_size_x = 16, local_size_y = 16, local_size_z = 1) in;

#define ASPECT_RATIO 1
#define SCREEN_SIZE vec2(2048, 2048)
#pragma include "../../rpcore/shader/includes/noise.inc.glsl"

uniform layout(rgba8) image2D DestTex;

float generate_grain(vec2 texCoord, vec2 resolution, float frame, float multiplier) {
    vec2 mult = texCoord * resolution;
    float offset = snoise3D(vec3(mult / multiplier, frame));
    float n1 = pnoise3D(vec3(mult, offset), vec3(1.0/texCoord * resolution, 1.0));
    return n1 * 0.5 + 0.5;
}

void main() {
  vec2 texcoord = vec2(ivec2(gl_GlobalInvocationID.xy) + 0.5) / 2048.0;
  vec4 result = vec4(generate_grain(texcoord * 2048.0, vec2(4096.0), 0.0, 4.634523));
  imageStore(DestTex, ivec2(gl_GlobalInvocationID.xy), result);
}
