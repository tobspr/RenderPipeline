#version 420

#define USE_MAIN_SCENE_DATA
#pragma include "Includes/Configuration.inc.glsl"
#pragma include "Includes/GBuffer.inc.glsl"

uniform GBufferData GBuffer;
uniform sampler2D CurrentTex;
uniform sampler2D LastTex;

out vec4 result;

void main() {

    vec2 texcoord = get_texcoord();
    ivec2 coord = ivec2(gl_FragCoord.xy);

    vec2 velocity = get_gbuffer_velocity(GBuffer, texcoord);
    vec2 old_coord = texcoord - velocity;
    vec4 current_color = textureLod(CurrentTex, texcoord, 0);
    vec4 last_color = textureLod(LastTex, old_coord, 0);

    float weight = 0.5;

    // Out of screen
    if (old_coord.x < 0.0 || old_coord.x > 1.0 || old_coord.y < 0.0 || old_coord.y > 1.0) {
        weight = 0.0;
    }

    // Fade out when velocity gets too big
    const float max_velocity = 15.0 / WINDOW_HEIGHT; 
    weight *= 1.0 - saturate(length(velocity) / max(0.000001, max_velocity));

    result = mix(current_color, last_color, weight);
}
