#version 400

#pragma include "Includes/Configuration.inc.glsl"

in vec2 texcoord;
in vec4 cloudcolor;
out vec4 result;
uniform sampler2D SpriteTex;

void main() {
    float alpha = texture(SpriteTex, texcoord).x;
    if (alpha * cloudcolor.w < 0.2) discard;
    result = vec4(cloudcolor.xyz, 1);
}
