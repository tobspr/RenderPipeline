/**
 *
 * RenderPipeline
 *
 * Copyright (c) 2014-2016 tobspr <tobias.springer1@gmail.com>
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 * THE SOFTWARE.
 *
 */

#version 400

#define USE_MAIN_SCENE_DATA
#define USE_TIME_OF_DAY
#pragma include "render_pipeline_base.inc.glsl"

#define USE_GBUFFER_EXTENSIONS
#pragma include "includes/gbuffer.inc.glsl"
#pragma include "includes/light_culling.inc.glsl"
#pragma include "includes/noise.inc.glsl"

uniform sampler2D NoiseTex;
uniform sampler3D CloudVoxels;

out vec4 result;

#define CLOUD_RES_Z 64
#define CLOUD_RES_XY 512

const float KM = 1000.0;
const float METER = 1.0;

const float earth_radius = 6371.0 * KM;
const vec3 earth_mid = vec3(0, 0, -earth_radius);
const float cloud_start = earth_radius + 1.0 * KM;
const float cloud_end = earth_radius + 1.4 * KM;

vec2 get_cloud_coord(vec3 pos) {
    vec2 xy_coord = pos.xy / (cloud_end - cloud_start) * float(CLOUD_RES_Z) / float(CLOUD_RES_XY);
    xy_coord.xy /= 1.0 + 0.5 * length(xy_coord);
    xy_coord.xy += 0.5;
    return xy_coord;
}

void main() {
    const int trace_steps = GET_SETTING(clouds, raymarch_steps);
    // const int trace_steps = 64;

    vec2 texcoord = get_half_texcoord();

    vec3 wind_offs = vec3(0.2, 0.3,0) * 0.02 * MainSceneData.frame_time;

    vec3 pos = get_gbuffer_position(GBuffer, texcoord);
    vec3 ray_start = MainSceneData.camera_pos;
    vec3 ray_dir = normalize(pos - ray_start);

    if (!is_skybox(pos) || ray_dir.z < 0.0) {
        result = vec4(0);
        return;
    }

    float t_low, t_high, tmp;

    // Intersect with lower bounds plane to get starting point
    // float t_low = -(ray_start.z - 3000.0) / ray_dir.z;
    // float t_high = -(ray_start.z - 4000.0) / ray_dir.z;

    bool rb = ray_sphere_intersection(earth_mid, cloud_start, ray_start, ray_dir, t_low, tmp);
    bool rt = ray_sphere_intersection(earth_mid, cloud_end, ray_start, ray_dir, t_high, tmp);


    if (t_low < 0.0) t_low = 0.0;
    if (t_high < 0.0 || distance(t_high, t_low) < 0.01) {
        result = vec4(0.2, 0, 0, 0);
        return;
    }

    float h_low = 0.0;
    float h_high = 1.0;

    // Get start and end in cloud space coordinates
    vec3 trace_start = vec3(get_cloud_coord(ray_start + t_low * ray_dir), h_low);
    vec3 trace_end = vec3(get_cloud_coord(ray_start + t_high * ray_dir), h_high);


    // Cloud noise
    float noise_factor = saturate(1.0 - 0.5 * length(trace_start.xy));
    vec3 noise = texture(NoiseTex, trace_start.xy * 25.0).xyz;
    noise = mix(vec3(0.5), noise, noise_factor);

    trace_start += wind_offs;
    trace_end += wind_offs;

    trace_start.xyz += (noise*2.0-1.0) * 0.002;
    vec3 trace_step = (trace_end - trace_start) / trace_steps;
    trace_step.xyz += (noise*2.0-1.0) * 0.004 / trace_steps;

    vec3 sun_vector = get_sun_vector();
    float sun_influence = pow(max(0, dot(ray_dir, sun_vector)), 15.0) + 0.0;
    vec3 sun_color = sun_influence * 40.0 * vec3(1);

    vec3 curr_pos = trace_start + 0.5 / vec3(CLOUD_RES_XY, CLOUD_RES_XY, CLOUD_RES_Z);
    float accum_weight = 0.0;
    vec3 accum_color = vec3(0);

    // Raymarch over the voxel texture
    for (int i = 0; i < trace_steps; ++i) {
        vec4 cloud_sample = texture(CloudVoxels, curr_pos);
        float weight = cloud_sample.x * (1.0 - accum_weight) * 0.6;
        accum_color += cloud_sample.yyy * weight;
        // accum_color += vec3(curr_pos.z) * weight;
        accum_weight += weight;
        curr_pos += trace_step;
    }

    // Beers law
    // accum_color = 1 - exp(-3.0 * accum_color);

    accum_color = pow(accum_color, vec3(0.6));

    // Unpack packed color
    // accum_color = accum_color / (1 - accum_color);
    // accum_color /= 15.0;
    // accum_weight *= 1 * length(accum_color);
    // accum_weight *= 0.4;
    // accum_weight = saturate(pow(accum_weight, 32.0) * 1.1);
    accum_color *= TimeOfDay.clouds.cloud_brightness;
    accum_color *= get_sun_color();

    // accum_color *= 1.8;
    // accum_color *= vec3(1.2, 1.1, 1);
    accum_color *= 0.4 + sun_color * saturate(1.0 - 0.8 * accum_weight );


    // Darken clouds in the distance
    // accum_color *= 1.0 - saturate(1.0-4.0*ray_dir.z) * 0.7;

    // Don't render clouds at obligue angles
    float horizon = pow(saturate(ray_dir.z * 4.0), 0.1);
    accum_color *= horizon;
    accum_weight *= horizon;

    // accum_weight = 0;

    result = vec4(accum_color, accum_weight);
    // result.xyz = vec3(accum_weight);
}
