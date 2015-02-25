#version 400

#define NO_EXTENDED_PACKING
#pragma include "Includes/Packing.include"
#pragma include "Includes/Configuration.include"

in vec2 texcoord;
in vec3 worldPos;
in vec3 diffuseMultiplier;
uniform sampler2D p3d_Texture0;

void main() {
    // Alpha test
    // vec4 tex_sample = texture(p3d_Texture0, texcoord);
    // if (tex_sample.a < 0.5) discard;
}
