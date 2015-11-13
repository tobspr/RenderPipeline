#version 400

#pragma optionNV (unroll all)

#pragma include "Includes/Configuration.inc.glsl"
#pragma include "Includes/PositionReconstruction.inc.glsl"
#pragma include "Includes/PoissonDisk.inc.glsl"

in vec2 texcoord;
out vec4 result;

uniform vec3 cameraPosition;
uniform sampler2D GBufferDepth;

uniform sampler2D Noise4x4;


// Functions which can be used by the kernels
float get_depth_at(vec2 coord) {
    return textureLod(GBufferDepth, coord, 0).x;
}

float get_depth_at(ivec2 coord) {
    return texelFetch(GBufferDepth, coord, 0).x;
}


vec3 get_view_pos_at(vec2 coord) {
    // vec2 tcoord = (coord + 0.5) / vec2(WINDOW_WIDTH, WINDOW_HEIGHT);
    return calculateViewPos(get_depth_at(coord), coord);

    // return textureLod(ViewSpacePosDepth, coord, 0).xyz;
}

vec3 get_view_pos_at(ivec2 coord) {
    vec2 tcoord = (coord + 0.5) / vec2(WINDOW_WIDTH, WINDOW_HEIGHT);
    return get_view_pos_at(tcoord);
}



vec3 get_pixel_normal(ivec2 coord) {

    vec3 view_pos = get_view_pos_at(coord);

    // Do some work to find a good view normal
    vec3 dx_px = view_pos - get_view_pos_at(coord + ivec2(1, 0));
    vec3 dx_py = view_pos - get_view_pos_at(coord + ivec2(0, 1));

    vec3 dx_nx = get_view_pos_at(coord + ivec2(-1, 0)) - view_pos;
    vec3 dx_ny = get_view_pos_at(coord + ivec2(0, -1)) - view_pos;

    // Find the closest normal
    vec3 dx_x = abs(dx_px.z) < abs(dx_nx.z) ? vec3(dx_px) : vec3(dx_nx);
    vec3 dx_y = abs(dx_py.z) < abs(dx_ny.z) ? vec3(dx_py) : vec3(dx_ny);

    vec3 nrm = normalize(cross(normalize(dx_x), normalize(dx_y)));
    return nrm;
}

void main() {

    result = vec4(1, 0, 0, 1);

    // Provide some variables to the kernel
    vec2 screen_size = vec2(WINDOW_WIDTH, WINDOW_HEIGHT);
    vec2 pixel_size = vec2(1.0) / screen_size;

    ivec2 coord = ivec2(gl_FragCoord.xy) * 2;

    vec3 pixel_normal = get_pixel_normal(coord);
    float pixel_depth = get_depth_at(coord);
    vec3 pixel_view_pos = get_view_pos_at(coord);

    vec3 material_pos = calculateSurfacePos(texelFetch(GBufferDepth, coord, 0).x, texcoord);
    vec3 view_vector = normalize(material_pos - cameraPosition);
    float view_dist = distance(material_pos, cameraPosition);

    vec3 noise_vec = texelFetch(Noise4x4, ivec2(gl_FragCoord.xy) % 4, 0).xyz * 2.0 - 1.0;


    if (view_dist > 10000.0) {
        result = vec4(1);
        return;
    }


    float kernel_scale = 10.0 / view_dist;

    const float sample_radius = GET_SETTING(AO, sample_radius); 
    
    // Include the appropriate kernel
    #if ENUM_V_ACTIVE(AO, technique, SSAO)

        #pragma include "../SSAO.kernel.glsl"

    #else

        #error Unkown AO technique!

    #endif

}


