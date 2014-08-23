#version 150
#pragma file "DefaultShadowCaster/fragment.glsl"



#define NO_EXTENDED_PACKING
#include "Includes/Packing.include"

in vec2 texcoord;
in vec3 worldPos;
in vec3 diffuseMultiplier;
uniform sampler2D p3d_Texture0;
out vec4 diffuse;
void main() {
    diffuse.rgb = texture(p3d_Texture0, texcoord).rgb * diffuseMultiplier;
    // diffuse.rgb = diffuseMultiplier;
    // diffuse.rgb -= 0.3;
    // diffuse.rgb = max(vec3(0), diffuse.rgb);
    diffuse.a = 1.0;
}