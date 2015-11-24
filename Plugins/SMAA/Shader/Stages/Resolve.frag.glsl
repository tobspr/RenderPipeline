#version 400

#pragma include "Includes/Configuration.inc.glsl"
#pragma include "Includes/GBufferPacking.inc.glsl"


uniform GBufferData GBuffer;
uniform sampler2D CurrentTex;
uniform sampler2D LastTex;

in vec2 texcoord;
out vec4 result;


void main() {

    ivec2 coord = ivec2(gl_FragCoord.xy);

    vec2 velocity = get_gbuffer_velocity(GBuffer, coord);
    vec2 old_coord = texcoord - velocity;
    vec4 current_color = texture(CurrentTex, texcoord);
    vec4 last_color = texture(LastTex, old_coord);


    // Blend the pixels according to the calculated weight:
    // return lerp(current, previous, weight);

    float weight = 0.5;

    // Out of screen
    if (old_coord.x < 0.0 || old_coord.x > 1.0 || old_coord.y < 0.0 || old_coord.y > 1.0) {
        weight = 0.0;
    }

    // Fade out when velocity gets too big
    const float max_velocity = 15.0 / WINDOW_HEIGHT; 
    weight *= 1.0 - saturate(length(velocity) / max_velocity);

    // weight = 1.0;
    // weight = 0.5;



    result = mix(current_color, last_color, weight);
    // result = vec4(length(velocity) * 4000.0);
    // result = vec4(weight);
}

