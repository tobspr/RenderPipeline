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
#pragma include "render_pipeline_base.inc.glsl"

#define USE_GBUFFER_EXTENSIONS
#pragma include "includes/gbuffer.inc.glsl"
#pragma include "includes/noise.inc.glsl"

uniform sampler2D ShadedScene;
uniform sampler2D CombinedVelocity;
uniform sampler2D Previous_PostAmbientScene;
uniform sampler2D DownscaledDepth;

out vec4 result;


/*

This plugin is BUGGY right now!

*/

vec4 trace_screen_ray(vec3 ro, vec3 ray_dir, float roughness) {
    // Don't trace rays facing towards the camera
    if (ray_dir.z <= 0.0) {
        return vec4(0);
    }

    ray_dir = normalize(ray_dir);
    ray_dir *= 0.4;

    const float hit_bias = 0.0001;

    int max_iter = int(16 + (1 - roughness) * 32);

    vec3 ray_start = ro + ray_dir * 0.005;
    float step_size = 1.0 / float(max_iter - 1);
    float hit_len = 0.0;
    float len = 0;
    float fade = 1.0;

    for (int i = 0; i < max_iter; ++i)
    {
        len += step_size;
        vec3 position = ray_start + len * ray_dir;
        // float pix_depth = texture(DownscaledDepth, position.xy).x;
        float pix_depth = get_gbuffer_depth(GBuffer, position.xy);
        if (abs(pix_depth - position.z) < hit_bias) {
            hit_len = len;
            break;
        }
    }

    fade = saturate(1.0 - hit_len);
    fade = sqrt(fade);

    if (hit_len > 0)
        return vec4(ray_start + hit_len * ray_dir, fade);

    return vec4(0);

}

vec4 trace_ray(Material m, vec3 ro, vec3 rd, vec2 texcoord)
{

    vec4 intersection = trace_screen_ray(ro, rd, m.roughness);
    if(intersection.w > 0.0 && distance(intersection.xy, texcoord) > 0.0001) {

        vec2 velocity = texture(CombinedVelocity, intersection.xy).xy;
        vec2 last_coord = intersection.xy + velocity;

        // Out of screen, can early out
        if (last_coord.x < 0.0 || last_coord.x >= 1.0 || last_coord.y < 0.0 || last_coord.y >= 1.0) {
            return vec4(0);
        }

        // TODO: Compute a weight based on the normal and depth/difference and so on

        vec3 intersected_color = texture(Previous_PostAmbientScene, last_coord).xyz;
        float fade_factor = intersection.w;
        fade_factor *= pow(saturate(35.0 * rd.z), 1.0);
        return vec4(intersected_color, 1) * fade_factor;
    }
    return vec4(0);
}


vec3 get_ray_direction(vec3 position, vec3 normal, vec3 view_dir, vec3 ro) {
    vec3 reflected_dir = reflect(view_dir, normal);
    float scale_factor = 0.1 +
        saturate(distance(position, MainSceneData.camera_pos) / 1000.0) * 0.5;

    vec3 target_pos = position + reflected_dir * scale_factor;
    vec3 screen_pos = world_to_screen(target_pos);
    return normalize(screen_pos - ro);


}

void main() {

    vec4 sslr_result = vec4(0);
    vec2 texcoord = get_texcoord();

    Material m = unpack_material(GBuffer);
    vec3 view_dir = normalize(m.position - MainSceneData.camera_pos);

    // float pixel_depth = textureLod(DownscaledDepth, texcoord, 0).x;
    float pixel_depth = get_gbuffer_depth(GBuffer, texcoord);


    if (distance(m.position, MainSceneData.camera_pos) > 10000) {
        result = vec4(0);
        return;
    }

    vec3 ray_origin = vec3(texcoord, pixel_depth);

    vec3 offs[8] = vec3[](
        vec3(-0.134, 0.044, -0.825),
        vec3(0.045, -0.431, -0.529),
        vec3(-0.537, 0.195, -0.371),
        vec3(0.525, -0.397, 0.713),
        vec3(0.895, 0.302, 0.139),
        vec3(-0.613, -0.408, -0.141),
        vec3(0.307, 0.822, 0.169),
        vec3(-0.819, 0.037, -0.388)
    );

    // int num_rays = int(sqrt(m.roughness) * 8);
    const int num_rays = 8;
    vec3 jitter = rand_rgb(vec2(mod(gl_FragCoord.x, 4.0), mod(gl_FragCoord.y, 4.0))) * 2 - 1;
    jitter *= 0.1;

    for (int i = 0; i < num_rays; i++) {
        vec3 ray_direction = get_ray_direction(m.position, normalize(m.normal + (offs[i] + jitter) * 0.25 * m.roughness), view_dir, ray_origin);
        sslr_result += trace_ray(m, ray_origin, ray_direction, texcoord);
    }

    result = sslr_result / num_rays;
    // result.xyz = result.www;
    result.w = saturate(result.w);
}
