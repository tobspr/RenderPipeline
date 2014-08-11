#version 150
#pragma file "DefaultShadowCaster/fragment.glsl"



#define NO_EXTENDED_PACKING
#include "Includes/Packing.include"

in vec2 texcoord;
in vec3 normal;
uniform sampler2D p3d_Texture0;

out vec4 diffuse;
out vec4 pixelNormal;

void main() {
    diffuse.rgb = texture(p3d_Texture0, texcoord).rgb;
    pixelNormal.rgb = normal.rgb*0.25 + 0.5;

    // pixelNormal.rgb = vec3(1);
    // diffuse.rgb = vec3(1);

    diffuse.a = 1.0;
    pixelNormal.a = 1.0;
}