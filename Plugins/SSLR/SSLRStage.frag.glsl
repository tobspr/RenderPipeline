
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

uniform vec3 cameraPosition;

uniform mat4 currentViewProjMat;
in vec2 texcoord;
out vec4 result;


void main() { 

    
    Material m = unpack_material(GBufferDepth, GBuffer0, GBuffer1, GBuffer2);
    vec3 view_dir = normalize(m.position - cameraPosition);

    vec3 reflected_dir = reflect(view_dir, m.normal );

    vec3 target_pos = m.position + reflected_dir * 0.5;
    vec4 transformed_pos = currentViewProjMat * vec4(target_pos, 1);
    transformed_pos.xyz /= transformed_pos.w;
    transformed_pos.xyz = transformed_pos.xyz * 0.5 + 0.5;

    vec3 curr_pos = vec3(texcoord, textureLod(DownscaledDepth, texcoord, 0).x);
    vec3 raydir = normalize(transformed_pos.xyz - curr_pos);
    // curr_pos += raydir * 0.001;
    vec3 sslr_result = vec3(0);

    bool hit = true;

    int mip = 0;
    int num_iter = 256;
    vec2 mip_size = vec2(WINDOW_WIDTH, WINDOW_HEIGHT);

    float movebias = 0.01;
    float searchbias = 0.00;

    float mc_x = 1.0 / abs(raydir.x);
    float mc_y = 1.0 / abs(raydir.x);


    while (mip > -1 && mip < 10 && num_iter --> 0) {
        
        // Find fraction of pixel coordinate
        vec2 fract_coord = fract(curr_pos.xy * mip_size);

        // Find out wheter to march up or down
        float step_x = raydir.x > 0.0 ? 1.0 - fract_coord.x : fract_coord.x;
        float step_y = raydir.y > 0.0 ? 1.0 - fract_coord.y : fract_coord.y;

        // Divide by the mip size since we multiplied by that before
        step_x /= mip_size.x;
        step_y /= mip_size.y;
        
        // Normalize the offset by the raymarch direction
        step_x /= abs(raydir.x);
        step_y /= abs(raydir.y);

        // March by the smallest distance required to move to the 
        // next cell. A small bias is used to make sure we actually move
        // into the next cell.
        float step_c = min(mc_x / mip_size.x, mc_y / mip_size.y);

        float final_step = min(step_x, step_y);
        curr_pos += raydir * final_step * (1.0 + movebias);

        float depth_bias = raydir.z * step_c;

        // curr_pos = saturate(curr_pos);
        // depth_bias = 0.0;

        vec2 cell_z = textureLod(DownscaledDepth, curr_pos.xy, mip).xy;
        float cell_min = cell_z.x;
        float cell_max = cell_z.y;

        float start_z = curr_pos.z;
        float end_z = start_z + depth_bias;

        // Intersection
        if (start_z > cell_min || end_z > cell_min) {
            if (start_z < cell_max || end_z < cell_max) {
                // hit = true;
                break;
            } else {
                mip --;
                mip_size *= 2.0;
            }
        } else {
            mip ++;
            mip_size /= 2.0;
        }


        // // Increase mip level?
        // if (depth_diff < 0.0) {
        //     mip ++;
        //     mip_size /= 2.0;
        // } 

        // // Decrease mip level?
        // if (depth_diff > 0.0) {
        //     mip --;
        //     mip_size *= 2.0;
        // }
    }


    if (hit) {
        if (any(lessThan(curr_pos.xy, vec2(0))) || any(greaterThan(curr_pos.xy, vec2(1)))) {

        } else {        

            vec3 hit_normal = normalize(texture(GBuffer1, curr_pos.xy).xyz);

            if (dot(hit_normal, m.normal) > 0.8) {

            } else {
                sslr_result = texture(ShadedScene, curr_pos.xy).xyz;
            }
        }
    }

    // sslr_result = vec3( mip / 5.0);



    result = texture(ShadedScene, texcoord);
    result.xyz = sslr_result;
}