#version 400

#pragma include "Includes/Configuration.inc.glsl"
#pragma include "Includes/PositionReconstruction.inc.glsl"

out vec4 result;
out vec4 result_nrm;
uniform sampler2D GBufferDepth;


vec3 get_view_pos(ivec2 coord) {
    vec2 tcoord = (coord + 0.5) / vec2(WINDOW_WIDTH, WINDOW_HEIGHT);
    return calculateViewPos(textureLod(GBufferDepth, tcoord, 0).x, tcoord);
}

void main() {
    ivec2 coord = ivec2(gl_FragCoord.xy);
    vec3 view_pos = get_view_pos(coord + ivec2(0, 0));
    
    float view_depth = texelFetch(GBufferDepth, coord, 0).x;

    // Do some work to find a good view normal
    vec3 view_pos_dxp = get_view_pos(coord + ivec2(1, 0));
    vec3 view_pos_dyp = get_view_pos(coord + ivec2(0, 1));

    vec3 view_pos_dxn = get_view_pos(coord + ivec2(-1, 0));
    vec3 view_pos_dyn = get_view_pos(coord + ivec2(0, -1));

    vec3 dx_px = view_pos - view_pos_dxp;
    vec3 dx_py = view_pos - view_pos_dyp;

    vec3 dx_nx = view_pos_dxn - view_pos;
    vec3 dx_ny = view_pos_dyn - view_pos;

    // Find the closest normal
    vec3 dx_x = abs(dx_px.z) < abs(dx_nx.z) ? vec3(dx_px) : vec3(dx_nx);
    vec3 dx_y = abs(dx_py.z) < abs(dx_ny.z) ? vec3(dx_py) : vec3(dx_ny);

    vec3 nrm = normalize(cross(normalize(dx_x), normalize(dx_y)));

    result = vec4(view_pos, view_depth);
    result_nrm = vec4(nrm, 1);
}