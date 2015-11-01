#version 430

#pragma include "Includes/Configuration.inc.glsl"
#pragma include "Includes/GBufferPacking.inc.glsl"

in vec2 texcoord;

uniform sampler2D Previous_ShadedScene;
uniform sampler2D GBuffer2;

out vec4 result;

void main() {

    ivec2 coord = ivec2(gl_FragCoord.xy);
    vec2 velocity = get_velocity(GBuffer2, coord);
    vec2 proj_coord = texcoord - velocity;


    if (proj_coord.x <= 0.0 || proj_coord.y <= 0.0 || proj_coord.x >= 1.0 || proj_coord.y >= 1.0) {
        result = vec4(1, 0, 0, 0);
        return;
    }
    
    vec4 sceneColor = texture(Previous_ShadedScene, proj_coord);

    result.xyz = sceneColor.xyz; 
    result.w = 1.0;
}

