#version 400

#pragma optionNV (unroll all)

#pragma include "Includes/Configuration.inc.glsl"
#pragma include "Includes/PositionReconstruction.inc.glsl"
#pragma include "Includes/PoissonDisk.inc.glsl"

in vec2 texcoord;
out vec4 result;

uniform vec3 cameraPosition;
uniform sampler2D GBufferDepth;

uniform sampler2D ViewSpacePosDepth;
uniform sampler2D ViewSpaceNormals;

// Functions which can be used by the kernels

vec3 get_view_nrm_at(vec2 coord) {
    return textureLod(ViewSpaceNormals, coord, 0).xyz;
}

vec3 get_view_nrm_at(ivec2 coord) {
    return texelFetch(ViewSpaceNormals, coord, 0).xyz;
}

vec4 get_view_pos_depth_at(vec2 coord) {
    // xyz: Normal w: Depth
    return textureLod(ViewSpacePosDepth, coord, 0);
}

vec4 get_view_pos_depth_at(ivec2 coord) {
    // xyz: Normal w: Depth
    return texelFetch(ViewSpacePosDepth, coord, 0);
}

float get_depth_at(vec2 coord) {
    return textureLod(ViewSpacePosDepth, coord, 0).w;
}

float get_depth_at(ivec2 coord) {
     return texelFetch(ViewSpacePosDepth, coord, 0).w;
}


void main() {

    result = vec4(1, 0, 0, 1);

    // Provide some variables to the kernel
    vec2 screen_size = vec2(WINDOW_WIDTH, WINDOW_HEIGHT);
    vec2 pixel_size = vec2(1.0) / screen_size;

    ivec2 coord = ivec2(gl_FragCoord.xy) * 2;

    vec3 pixel_normal = get_view_nrm_at(coord);
    vec4 pixel_data = get_view_pos_depth_at(coord);
    float pixel_depth = pixel_data.w;
    vec3 pixel_view_pos = pixel_data.xyz;

    vec3 material_pos = calculateSurfacePos(texelFetch(GBufferDepth, coord, 0).x, texcoord);
    vec3 view_vector = normalize(material_pos - cameraPosition);
    float view_dist = distance(material_pos, cameraPosition);

    if (view_dist > 10000.0) {
        result = vec4(1);
        return;
    }


    float kernel_scale = 10.0 / view_dist;

    const float sample_radius = GET_SETTING(AO, sample_radius); 

    // Include the appropriate kernel
    #if ENUM_V_ACTIVE(AO, technique, SSAO)

        #pragma include "../SSAO.kernel.glsl"

    #endif

    // result = vec4(pixel_noram, 0);

    // Get setting
    // const float tangent_bias = GET_SETTING(AO, tangent_bias);

    // const float max_sampling_radius = 0.4;

    // vec2 sample_coord = texcoord;
    // ivec2 coord = ivec2(gl_FragCoord).xy;

    // float depth = texelFetch(GBufferDepth, coord * 2, 0).x;
    // vec3 surface_pos = calculateSurfacePos(depth, sample_coord);
    // float surface_scale = distance(surface_pos, cameraPosition);

    // vec2 sample_radius = vec2(GET_SETTING(AO, sample_radius)) / vec2(WINDOW_WIDTH, WINDOW_HEIGHT);

    // // Get an uniform distribution
    // sample_radius *= 10.0 / surface_scale;

    // float averaged_samples = 0.0;

    // const int num_radii = GET_SETTING(AO, ray_count);
    // const int num_raymarch = GET_SETTING(AO, ray_steps);

    // vec4 mid_data = texelFetch(DepthSource, coord, 0);
    // vec3 mid_vp = mid_data.xyz;

    // // Extract view normal from view position
    // vec3 mid_nrm =  texelFetch(NrmSource, coord, 0).xyz;


    // result.xyz = mid_nrm;

    // // Sample in spherical coordinates
    // for (int i = 0; i < num_radii; ++i) {

    //     // Compute the angle, and the vector pointing into that direction
    //     float phi = (i / float(num_radii)) * TWO_PI;
    //     vec2 sample_dir = vec2(cos(phi), sin(phi));

    //     // TODO: Get that acos out of there
    //     float tangent_angle = acos(dot(vec3(sample_dir.xy, 0), mid_nrm)) - HALF_PI + tangent_bias;
    //     float max_angle = tangent_angle;

    //     // Store last difference
    //     vec3 last_diff = vec3(0);

    //     for (int k = 0; k < num_raymarch; ++k) {
    //         float theta = (k + 1) / float(num_raymarch);
    //         vec2 offcoord = texcoord + sample_dir * theta * sample_radius;

    //         vec4 data = textureLod(DepthSource, offcoord, 0);
    //         vec3 vp_diff = data.xyz - mid_vp;

    //         float factor = length(vp_diff) / GET_SETTING(AO, max_sample_distance);
            
    //         if (factor < 1.0) {
    //             last_diff = vp_diff;

    //             float angle = atan(vp_diff.z / length(vp_diff.xy)  );
    //             max_angle = max(max_angle, angle);
    //         }
    //     }


    //     // Compute attenuation, use difference of ray end for that
    //     float attenuation = 1.0 / (1 + length(last_diff.xy));
    //     float occlusion = saturate(attenuation * (sin(max_angle) - sin(tangent_angle)));
    //     averaged_samples += occlusion;
    // }

    // averaged_samples /= num_radii;
    // averaged_samples = pow(averaged_samples * 1.0, 1.0);

    // result = vec4(1 - saturate(averaged_samples));
}

