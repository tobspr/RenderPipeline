#version 400

#define USE_MAIN_SCENE_DATA
#define USE_TIME_OF_DAY
#pragma include "Includes/Configuration.inc.glsl"

#define USE_GBUFFER_EXTENSIONS
#pragma include "Includes/GBuffer.inc.glsl"
#pragma include "Includes/LightCulling.inc.glsl"
#pragma include "Includes/Noise.inc.glsl"

uniform sampler3D CloudVoxels;
out vec4 result;

const float KM = 1000.0;
const float METER = 1.0;

const float earth_radius = 6371.0 * KM;
const vec3 earth_mid = vec3(0, 0, -earth_radius);
const float cloud_start = earth_radius + 0.5 * KM;
const float cloud_end = earth_radius + 0.9 * KM;

vec2 get_cloud_coord(vec3 pos) {
    vec2 xy_coord = pos.xy / (cloud_end - cloud_start) * float(CLOUD_RES_Z) / float(CLOUD_RES_XY);
    // xy_coord *= 8.5;
    xy_coord += 0.5;

    return xy_coord;
}

void main() {
    const int trace_steps = 128;

    vec3 pos = get_gbuffer_position(GBuffer, ivec2(gl_FragCoord.xy) * 2);
    vec3 ray_start = MainSceneData.camera_pos;
    vec3 ray_dir = normalize(pos - ray_start);

    if (!is_skybox(pos, MainSceneData.camera_pos) || ray_dir.z < -0.0) {
        result = vec4(0);
        return;
    }
    // Intersect with lower bounds plane to get starting point
    float tmp;
    float t_low, t_high;
    ray_sphere_intersection(earth_mid, cloud_start, ray_start, ray_dir, t_low, tmp);
    ray_sphere_intersection(earth_mid, cloud_end, ray_start, ray_dir, t_high, tmp);

    if (t_high < 0.0 || t_low < 0.0 || distance(t_high, t_low) < 0.01) {
        result = vec4(0.1, 0, 0, 0);
        return;
    }

    // Get start and end in cloud space coordinates
    vec3 trace_start = vec3(get_cloud_coord(ray_start + t_low * ray_dir), 0);
    vec3 trace_end = vec3(get_cloud_coord(ray_start + t_high * ray_dir), 1);
    vec3 trace_step = (trace_end - trace_start) / trace_steps;

    // Get sun vector
    vec3 sun_vector = sun_azimuth_to_angle(
    TimeOfDay.Scattering.sun_azimuth,
    TimeOfDay.Scattering.sun_altitude);
    float sun_influence = pow(max(0, dot(ray_dir, sun_vector)), 45.0);
    vec3 sun_color = sun_influence * 40.0 * TimeOfDay.Scattering.sun_color;
        // vec3 sun_color = TimeOfDay.Scattering.sun_color * 

    vec3 curr_pos = trace_start + 0.5 / vec3(CLOUD_RES_XY, CLOUD_RES_XY, CLOUD_RES_Z);
    float accum_weight = 0.0;
    vec3 accum_color = vec3(0);

    // Raymarch over the voxel texture
    for (int i = 0; i < trace_steps; ++i) {
        vec4 cloud_sample = texture(CloudVoxels, curr_pos);
        float weight = cloud_sample.w * (1.0 - accum_weight);
        accum_color += cloud_sample.xyz * weight;
        accum_weight += weight;
        curr_pos += trace_step;
    }

    // Unpack packed color
    accum_color = accum_color / (1 - accum_color);
    accum_color /= 5.0;

    accum_color *= 130.0;
    accum_color *= 1 + sun_color * saturate(1.0 - 1.0 * accum_weight * accum_weight );
    // accum_weight *= 2.0;
    // accum_weight = saturate(accum_weight);
    // accum_weight *= 0.5;

    // Brighten clouds in the distance
    // accum_color *= 1.0 + saturate(1.0-5.0*ray_dir.z) * 3.0;

    // Don't render clouds at obligue angles
    float horizon = saturate(sqrt(ray_dir.z * 16.0));
    accum_weight *= horizon;
    // accum_color *= horizon;

    result = vec4(accum_color, accum_weight);
}