#version 400

#define USE_MAIN_SCENE_DATA
#pragma include "Includes/Configuration.inc.glsl"

#define USE_GBUFFER_EXTENSIONS
#pragma include "Includes/GBuffer.inc.glsl"

uniform sampler2D ShadedScene;
uniform sampler2D DownscaledDepth;

out vec4 result;


/*

This plugin is BUGGY right now!

*/

vec3 trace_ray_fast(vec3 ro, vec3 ray_dir) {
    // Don't trace rays facing towards the camera
    if (ray_dir.z <= 0.0) {
        return vec3(0);
    }

    const float hit_bias = 0.00001;
    const int max_iter = 32;

    ray_dir = ray_dir * 0.5; 

    vec3 position = ro + normalize(ray_dir) * 0.001;
    vec3 ray_step = ray_dir / float(max_iter);

    for(int i = 0; i < max_iter; ++i)
    {
        position += ray_step;
        float pix_depth = get_gbuffer_depth(GBuffer, position.xy);

        if (pix_depth < position.z + hit_bias) return position;

    }
    return vec3(0);

}

vec3 trace_ray(Material m, vec3 ro, vec3 rd, vec2 texcoord)
{

    vec3 intersection = trace_ray_fast(ro, rd);
    if(length(intersection) > 0.0001 && distance(intersection.xy, texcoord) > 0.00001) {

        vec3 intersected_color = textureLod(ShadedScene, intersection.xy, 0).xyz;
        vec3 intersected_normal = get_gbuffer_normal(GBuffer, intersection.xy);

        float dprod = dot(intersected_normal, m.normal);
        float fade_factor = 1.0 - saturate( (dprod) * 3.5);
        fade_factor = pow(saturate(35.0 * rd.z), 1.0);
        return mix(vec3(1.0), intersected_color * 20.0, fade_factor);
        // return intersected_color * 2.0;
    }

    return vec3(1);


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

    
    vec3 sslr_result = vec3(0);
    vec2 texcoord = get_texcoord();

    Material m = unpack_material(GBuffer);
    vec3 view_dir = normalize(m.position - MainSceneData.camera_pos);

    // float pixel_depth = textureLod(DownscaledDepth, texcoord, 0).x;
    float pixel_depth = get_gbuffer_depth(GBuffer, texcoord);

    if (distance(m.position, MainSceneData.camera_pos) > 10000) {
        sslr_result = vec3(1);
    } else {

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

        // for (int i = 0; i < 1; i++) {

            // vec3 jo = vec3( mod(gl_FragCoord.x, 2.0), mod(gl_FragCoord.y, 2.0), 0.0 );

            // vec3 ray_direction = get_ray_direction(m.position, normalize(m.normal + (offs[i] +jo) * 0.03 * 0), view_dir, ray_origin);
            vec3 ray_direction = get_ray_direction(m.position, m.normal, view_dir, ray_origin);

            sslr_result = trace_ray(m, ray_origin, ray_direction, texcoord);
            // sslr_result += ray_direction;
        // }

        // sslr_result /= 1.0;


        // sslr_result += trace_ray_smart(m, ray_origin, ray_direction);
        // sslr_result += trace_ray_smart(m, ray_origin, ray_direction);
        // sslr_result += trace_ray_smart(m, ray_origin, ray_direction);

        // vec3 intersection_coord = trace_ray(ray_origin, ray_direction);
        // intersection_coord.z = 0.0;
        // if (length(intersection_coord) > 0.001) {
        // sslr_result = textureLod(ShadedScene, intersection_coord.xy, 0).xyz;
        // }
        // sslr_result = intersection_coord;

    }



    result = textureLod(ShadedScene, texcoord, 0);
    result.xyz *= sslr_result;
    // result.xyz = sslr_result;
}