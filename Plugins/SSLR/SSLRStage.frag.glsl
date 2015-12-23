
#version 400

// #pragma optionNV (unroll all)

#pragma include "Includes/Configuration.inc.glsl"
#pragma include "Includes/GBufferPacking.inc.glsl"

uniform sampler2D ShadedScene;
uniform sampler2D GBufferDepth;
uniform sampler2D GBuffer0;
uniform sampler2D GBuffer1;
uniform sampler2D GBuffer2;

uniform sampler2D DownscaledDepth;

in vec2 texcoord;
out vec4 result;


vec3 trace_ray(vec3 ray_start, vec3 ray_dir)
{   

    // Don't trace rays facing towards the camera
    if (ray_dir.z < 0.0) {
        return vec3(0);
    }

    // Raytracing constants
    const int loop_max = 128;
    const float ray_epsilon = 1.0005;
    const float hit_bias = 0.001;

    // Limit the maximum amount of mipmaps. This important, choosing a too
    // high value will introduce artifacts.
    const int max_mips = 2;

    // Iteration parameters
    int mipmap = 0;
    int max_iter = loop_max;
    ivec2 work_size = SCREEN_SIZE_INT;
    ray_dir = normalize(ray_dir);
    vec3 pos = ray_start;

    // Move pos by a small bias to avoid self intersection
    pos += ray_dir * 0.005;


    while (mipmap > -1 && max_iter --> 0)
    {

        // Check if we are out of screen bounds, if so, return
        if (pos.x < 0.0 || pos.y < 0.0 || pos.x > 1.0 || pos.y > 1.0)
        {
            return vec3(0);
        }

        work_size = textureSize(DownscaledDepth, mipmap).xy;

   
        // Compute the fractional part of the coordinate (scaled by the working size)
        // so the values will be between 0.0 and 1.0
        vec2 fract_coord = mod(pos.xy * work_size, 1.0);

        // Modify fract coord based on which direction we are stepping in.
        // Fract coord now contains the percentage how far we moved already in
        // the current cell in each direction.  
        fract_coord.x = ray_dir.x > 0.0 ? fract_coord.x : 1.0 - fract_coord.x;
        fract_coord.y = ray_dir.y > 0.0 ? fract_coord.y : 1.0 - fract_coord.y;

        // Compute maximum k and minimum k for which the ray would still be
        // inside of the cell.
        vec2 max_k_v = (1.0 / abs(ray_dir.xy)) / work_size.xy;
        vec2 min_k_v = -max_k_v * fract_coord.xy;

        // Scale the maximum k by the percentage we already processed in the current cell,
        // since e.g. if we already moved 50%, we can only move another 50%.
        max_k_v *= 1.0 - fract_coord.xy;

        // The maximum k is the minimum of the both sub-k's since if one component-maximum
        // is reached, the ray is out of the cell
        float max_k = min(max_k_v.x, max_k_v.y) + hit_bias;

        // Same applies to the min_k, but because min_k is negative we have to use max()
        float min_k = min(min_k_v.x, min_k_v.y) - hit_bias;

        // Fetch the current minimum cell plane height
        float cell_z = textureLod(DownscaledDepth, pos.xy, mipmap).x;
        
        // Check if the ray intersects with the cell plane. We have the following
        // equation: 
        // pos.z + k * ray_dir.z = cell.z
        // So k is:
        float k = (cell_z - pos.z) / ray_dir.z;

        // Check if we intersected the cell
        if (k < max_k)
        {

            // Optional: Abort when ray didn't exactly intersect:
            // if (k < 0.0 && mipmap <= 0) {
                // return vec3(0);
            // } 

            // Clamp k
            k = max(min_k, k);
 
            if (mipmap <= 0) {
                pos += k * ray_dir * ray_epsilon;
                return pos;
            }

            // If we hit anything at a higher mipmap, step up to a higher detailed
            // mipmap:
            mipmap -= 1;
        } else {
            // If we hit nothing, move to the next cell and mipmap, with a small bias

            pos += max_k * ray_dir * ray_epsilon;

            mipmap = min(mipmap + 1, max_mips);
        }
    }
    return vec3(0);
}





vec3 trace_ray_fast(vec3 ro, vec3 ray_dir) {


    // Don't trace rays facing towards the camera
    if (ray_dir.z <= 0.0) {
        return vec3(0);
    }

    const int mipmap = 4;
    const float ray_epsilon = 1.0005;
    const float hit_bias = 0.01;
    ivec2 work_size = textureSize(DownscaledDepth, mipmap).xy;

    ray_dir = normalize(ray_dir);
    vec3 pos = ro;

    int max_iter = 50;

    pos += ray_dir * 0.05;

    while (max_iter --> 0)
    {

        // Check if we are out of screen bounds, if so, return
        if (pos.x < 0.0 || pos.y < 0.0 || pos.x > 1.0 || pos.y > 1.0)
        {
            return vec3(0);
        }
   
        // Compute the fractional part of the coordinate (scaled by the working size)
        // so the values will be between 0.0 and 1.0
        vec2 fract_coord = mod(pos.xy * work_size, 1.0);

        // Modify fract coord based on which direction we are stepping in.
        // Fract coord now contains the percentage how far we moved already in
        // the current cell in each direction.  
        fract_coord.x = ray_dir.x > 0.0 ? fract_coord.x : 1.0 - fract_coord.x;
        fract_coord.y = ray_dir.y > 0.0 ? fract_coord.y : 1.0 - fract_coord.y;

        // Compute maximum k and minimum k for which the ray would still be
        // inside of the cell.
        vec2 max_k_v = (1.0 / abs(ray_dir.xy)) / work_size.xy;
        vec2 min_k_v = -max_k_v * fract_coord.xy;

        // Scale the maximum k by the percentage we already processed in the current cell,
        // since e.g. if we already moved 50%, we can only move another 50%.
        max_k_v *= 1.0 - fract_coord.xy;

        // The maximum k is the minimum of the both sub-k's since if one component-maximum
        // is reached, the ray is out of the cell
        float max_k = min(max_k_v.x, max_k_v.y) + hit_bias;

        // Same applies to the min_k, but because min_k is negative we have to use max()
        float min_k = max(min_k_v.x, min_k_v.y) - hit_bias;

        // Fetch the current minimum cell plane height
        vec2 cell_z = textureLod(DownscaledDepth, pos.xy, mipmap).xy;
        float zmin = cell_z.x;
        float zmax = cell_z.x;

        float zstart = pos.z + min_k * ray_dir.z;
        float zend = pos.z + max_k * ray_dir.z;

        // Check if the ray intersects with the cell plane. We have the following
        // equation: 
        // pos.z + k * ray_dir.z = cell.z
        // So k is:
        // float k = (cell_z - pos.z) / ray_dir.z;

        // float z_start = pos + k 

        // Check if we intersected the cell
        if ( (zstart > zmin && zstart < zmax) || (zend > zmin && zend < zmax) || (zstart < zmin && zstart > zmax) )
        {
            // Clamp k
            // k = max(min_k, k);
 
            pos += max_k * ray_dir * ray_epsilon;
            return pos;

        } 
        // If we hit nothing, move to the next cell and mipmap, with a small bias
        pos += max_k * ray_dir * ray_epsilon;


    }
    return vec3(0);

}



vec3 trace_ray_smart(Material m, vec3 ro, vec3 rd)
{

    vec3 intersection = trace_ray(ro, rd);
    // vec3 intersection = trace_ray_fast(ro, rd);
    if(length(intersection) > 0.0001 && distance(intersection.xy, texcoord) > 0.00001) {

        vec3 intersected_color = textureLod(ShadedScene, intersection.xy, 0).xyz;
        vec3 intersected_normal = get_gbuffer_normal(GBuffer1, intersection.xy);

        float dprod = dot(intersected_normal, m.normal);
        float fade_factor = 1.0 - saturate( (dprod) * 3.5);
        // fade_factor = step(dprod, 0.02);
        // fade_factor = 1.0;

        return intersected_color * fade_factor;
    }

    return vec3(0, 0, 0);


}


vec3 get_ray_direction(vec3 position, vec3 normal, vec3 view_dir, vec3 ro) {
    vec3 reflected_dir = reflect(view_dir, normal );

    float scale_factor = 0.1 + 
        saturate(distance(position, MainSceneData.camera_pos) / 1000.0) * 0.0;

    vec3 target_pos = position + reflected_dir * scale_factor;
    vec4 transformed_pos = MainSceneData.view_proj_mat_no_jitter * vec4(target_pos, 1);
    transformed_pos.xyz /= transformed_pos.w;
    transformed_pos.xyz = transformed_pos.xyz * 0.5 + 0.5;

    return normalize(transformed_pos.xyz - ro);


}

void main() { 

    
    vec3 sslr_result = vec3(0);

    Material m = unpack_material(GBufferDepth, GBuffer0, GBuffer1, GBuffer2);
    vec3 view_dir = normalize(m.position - MainSceneData.camera_pos);

    float pixel_depth = textureLod(DownscaledDepth, texcoord, 0).x;

    if (distance(m.position, MainSceneData.camera_pos) > 10000) {

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

        for (int i = 0; i < 1; i++) {

            vec3 jo = vec3( mod(gl_FragCoord.x, 2.0), mod(gl_FragCoord.y, 2.0), 0.0 );

            vec3 ray_direction = get_ray_direction(m.position, normalize(m.normal + (offs[i] +jo) * 0.00), view_dir, ray_origin);

            sslr_result += trace_ray_smart(m, ray_origin, ray_direction);
            // sslr_result += ray_direction;
        }

        sslr_result /= 1.0;



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
    result.xyz += sslr_result;
}