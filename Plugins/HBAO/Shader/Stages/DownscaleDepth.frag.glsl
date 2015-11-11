#version 400

#pragma include "Includes/Configuration.inc.glsl"
#pragma include "Includes/PositionReconstruction.inc.glsl"

out vec4 result;
uniform sampler2D GBufferDepth;


vec3 get_view_pos(ivec2 coord) {
    vec2 tcoord = (coord + 0.5) / vec2(WINDOW_WIDTH, WINDOW_HEIGHT);
    return calculateViewPos(textureLod(GBufferDepth, tcoord, 0).x, tcoord);
}

void main() {
    ivec2 coord = ivec2(gl_FragCoord.xy) * 2;
    vec3 view_pos = get_view_pos(coord + ivec2(0, 0));
    float view_depth = texelFetch(GBufferDepth, coord, 0).x;
    result = vec4(view_pos, view_depth);
}