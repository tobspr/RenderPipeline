#version 400

#pragma include "Includes/Configuration.inc.glsl"
#pragma include "Includes/GBufferPacking.inc.glsl"


uniform sampler2D GBuffer2;
uniform sampler2D CurrentTex;
uniform sampler2D LastTex;

in vec2 texcoord;
out vec4 result;


void main() {

    ivec2 coord = ivec2(gl_FragCoord.xy);

    vec2 velocity = get_velocity(GBuffer2, coord);
    vec2 old_coord = texcoord - velocity;
    vec4 current_color = texture(CurrentTex, texcoord);
    vec4 last_color = texture(LastTex, old_coord);

    float blend_factor = 0.5;

    result = mix(current_color, last_color, blend_factor);
}

