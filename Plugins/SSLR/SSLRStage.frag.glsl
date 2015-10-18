
#version 400

#pragma include "Includes/Configuration.inc.glsl"
#pragma include "Includes/GBufferPacking.inc.glsl"

uniform sampler2D ShadedScene;
uniform sampler2D GBufferDepth;
uniform sampler2D GBuffer0;
uniform sampler2D GBuffer1;
uniform sampler2D GBuffer2;

uniform vec3 cameraPosition;

uniform mat4 currentViewProjMat;
in vec2 texcoord;
out vec4 result;


void main() { 

    
    Material m = unpack_material(GBufferDepth, GBuffer0, GBuffer1, GBuffer2);
    vec3 view_dir = normalize(m.position - cameraPosition);

    vec3 reflected_dir = reflect(view_dir, m.normal);

    vec3 target_pos = m.position + reflected_dir * 5.0;
    vec4 transformed_pos = currentViewProjMat * vec4(target_pos, 1);
    transformed_pos.xyz /= transformed_pos.w;
    transformed_pos.xyz = transformed_pos.xyz * 0.5 + 0.5;

    vec3 curr_pos = vec3(texcoord, texture(GBufferDepth, texcoord).x);

    vec3 raydir = (transformed_pos.xyz - curr_pos) * 2.0;

    vec3 sslr_result = vec3(0);

    vec3 stepdir = raydir / 100.0;

    // curr_pos += stepdir * 1.0;
    bool hit = false;
    for (int i = 0; i < 100; i++) {
        
        float currd = texture(GBufferDepth, curr_pos.xy).x;
        float depth_d = curr_pos.z - currd;
        if (depth_d > 0.001 && depth_d < 0.05) {
            hit = true;
            break;
        }

        curr_pos += stepdir;
    }

    if (hit) {
        if (any(lessThan(curr_pos.xy, vec2(0))) || any(greaterThan(curr_pos.xy, vec2(1)))) {

        } else {        

            vec3 hit_normal = normalize(texture(GBuffer1, curr_pos.xy).xyz);

            if (dot(hit_normal, m.normal) > 0.7) {

            } else {
                sslr_result = texture(ShadedScene, curr_pos.xy).xyz;
            }
        }
    }

    // sslr_result = vec3(transformed_pos.z);



    result = texture(ShadedScene, texcoord);
    result.xyz += sslr_result;
}