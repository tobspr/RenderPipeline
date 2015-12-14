#version 400

#pragma optionNV (unroll all)

#pragma include "Includes/Configuration.inc.glsl"
#pragma include "Includes/PositionReconstruction.inc.glsl"
#pragma include "Includes/PoissonDisk.inc.glsl"
#pragma include "Includes/GBuffer.inc.glsl"

in vec2 texcoord;
out vec4 result;

uniform vec3 cameraPosition;
uniform GBufferData GBuffer;
uniform sampler2D Noise4x4;


// Functions which can be used by the kernels
float get_depth_at(vec2 coord) {
    return get_gbuffer_depth(GBuffer, coord);
}

float get_depth_at(ivec2 coord) {
    return get_gbuffer_depth(GBuffer, coord);
}

vec3 get_view_pos_at(vec2 coord) {
    return calculate_view_pos(get_depth_at(coord), coord);
}

vec3 get_view_pos_at(ivec2 coord) {
    vec2 tcoord = (coord + 0.5) / vec2(WINDOW_WIDTH, WINDOW_HEIGHT);
    return get_view_pos_at(tcoord);
}

vec3 get_world_pos_at(vec2 coord) {
    return calculate_surface_pos(get_depth_at(coord), coord);
}

vec3 get_world_pos_at(ivec2 coord) {
    vec2 tcoord = (coord + 0.5) / vec2(WINDOW_WIDTH, WINDOW_HEIGHT);
    return calculate_surface_pos(get_depth_at(tcoord), tcoord);
}


vec3 get_view_normal(ivec2 coord) {

    vec3 view_pos = get_view_pos_at(coord);

    // Do some work to find a good view normal
    vec3 dx_px = view_pos - get_view_pos_at(coord + ivec2(1, 0));
    vec3 dx_py = view_pos - get_view_pos_at(coord + ivec2(0, 1));

    vec3 dx_nx = get_view_pos_at(coord + ivec2(-1, 0)) - view_pos;
    vec3 dx_ny = get_view_pos_at(coord + ivec2(0, -1)) - view_pos;

    // Find the closest distance in depth
    vec3 dx_x = abs(dx_px.z) < abs(dx_nx.z) ? vec3(dx_px) : vec3(dx_nx);
    vec3 dx_y = abs(dx_py.z) < abs(dx_ny.z) ? vec3(dx_py) : vec3(dx_ny);

    return normalize(cross(normalize(dx_x), normalize(dx_y)));
}

void main() {

    result = vec4(1, 0, 0, 1);

    // Provide some variables to the kernel
    vec2 screen_size = vec2(WINDOW_WIDTH, WINDOW_HEIGHT);
    vec2 pixel_size = vec2(1.0) / screen_size;

    ivec2 coord = ivec2(gl_FragCoord.xy) * 2;

    // Shader variables
    float pixel_depth = get_depth_at(coord);
    vec3 pixel_view_pos = get_view_pos_at(coord);
    vec3 pixel_view_normal = get_view_normal(coord);
    vec3 pixel_world_pos = get_world_pos_at(coord);
    vec3 pixel_world_normal = get_gbuffer_normal(GBuffer, coord);

    vec3 view_vector = normalize(pixel_world_pos - cameraPosition);
    float view_dist = distance(pixel_world_pos, cameraPosition);

    vec3 noise_vec = texelFetch(Noise4x4, ivec2(gl_FragCoord.xy) % 4, 0).xyz * 2.0 - 1.0;

    if (view_dist > 10000.0) {
        result = vec4(1);
        return;
    }

    // float kernel_scale = 10.0 / get_linear_z_from_z(pixel_depth);
    float kernel_scale = 10.0 / view_dist;


    // Include the appropriate kernel
    #if ENUM_V_ACTIVE(AO, technique, SSAO)

        #pragma include "../SSAO.kernel.glsl"

    #elif ENUM_V_ACTIVE(AO, technique, HBAO)

        #pragma include "../HBAO.kernel.glsl"

    #elif ENUM_V_ACTIVE(AO, technique, SSVO)

        #pragma include "../SSVO.kernel.glsl"

    #elif ENUM_V_ACTIVE(AO, technique, ALCHEMY)

        #pragma include "../ALCHEMY.kernel.glsl"

    #elif ENUM_V_ACTIVE(AO, technique, UE4AO)

        #pragma include "../UE4AO.kernel.glsl"

    #else

        #error Unkown AO technique!

    #endif


    result.w = pow(result.w, GET_SETTING(AO, occlusion_strength));

    // Pack bent normal
    result.xyz = fma(result.xyz, vec3(0.5), vec3(0.5));
}


