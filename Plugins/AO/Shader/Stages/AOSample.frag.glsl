#version 420

#pragma optionNV (unroll all)

#define USE_MAIN_SCENE_DATA
#pragma include "Includes/Configuration.inc.glsl"
#pragma include "Includes/PositionReconstruction.inc.glsl"
#pragma include "Includes/PoissonDisk.inc.glsl"

flat in int instance;
in vec2 texcoord;
out vec4 result;

uniform sampler2D Noise4x4;

// use the extended gbuffer api
#define USE_GBUFFER_EXTENSIONS 1
#pragma include "Includes/GBuffer.inc.glsl"

void main() {

    result = vec4(1, 0, 0, 1);

    // Provide some variables to the kernel
    vec2 screen_size = vec2(WINDOW_WIDTH, WINDOW_HEIGHT);
    vec2 pixel_size = vec2(1.0) / screen_size;

    int ox = instance % 2;
    int oy = instance / 2;
    float disk_rotate = (instance / 4.0) * 180.0 / M_PI;

    ivec2 coord = ivec2(gl_FragCoord.xy) * 2 - ivec2(ox, oy) * SCREEN_SIZE_INT;

    // Shader variables
    float pixel_depth = get_depth_at(coord);
    vec3 pixel_view_pos = get_view_pos_at(coord);
    vec3 pixel_view_normal = get_view_normal(coord);
    vec3 pixel_world_pos = get_world_pos_at(coord);
    vec3 pixel_world_normal = get_gbuffer_normal(GBuffer, coord);


    vec3 view_vector = normalize(pixel_world_pos - MainSceneData.camera_pos);
    float view_dist = distance(pixel_world_pos, MainSceneData.camera_pos);

    vec3 noise_vec = texelFetch(Noise4x4, ivec2(ox, oy), 0).xyz * 2.0 - 1.0;

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


