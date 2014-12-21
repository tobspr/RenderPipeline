#version 400
#pragma file "DefaultShadowCaster/fragment.glsl"



#define NO_EXTENDED_PACKING
#include "Includes/Packing.include"
#include "Includes/Configuration.include"

in vec2 texcoord;
in vec3 worldPos;
in vec3 diffuseMultiplier;
uniform sampler2D p3d_Texture0;

#if USE_GLOBAL_ILLUMINATION
layout(location = 0) out vec4 gi_color;
#endif 

void main() {
    vec4 tex_sample = texture(p3d_Texture0, texcoord);
    // Alpha test
    if (tex_sample.a < 0.5) discard;
}