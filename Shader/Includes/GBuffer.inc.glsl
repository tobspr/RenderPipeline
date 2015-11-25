#pragma once

#pragma include "Includes/Configuration.inc.glsl"
#pragma include "Includes/Structures/Material.struct.glsl"


#define USE_NORMAL_QUANTIZATION 0
#pragma include "Includes/NormalQuantization.inc.glsl"



#if defined(IS_GBUFFER_SHADER)


    /*

    GBuffer Packing

    */


    uniform mat4 currentViewProjMatNoJitter;

    layout(location=0) out vec4 gbuffer_out_0;
    layout(location=1) out vec4 gbuffer_out_1;
    layout(location=2) out vec4 gbuffer_out_2;

    vec2 compute_velocity() {
        // Compute velocity based on this and last frames mvp matrix
        vec4 last_proj_pos = vOutput.last_proj_position;
        vec2 last_texcoord = fma(last_proj_pos.xy / last_proj_pos.w, vec2(0.5), vec2(0.5));
        vec4 curr_proj_pos = currentViewProjMatNoJitter * vec4(vOutput.position, 1);
        vec2 curr_texcoord = fma(curr_proj_pos.xy / curr_proj_pos.w, vec2(0.5), vec2(0.5));
        return (curr_texcoord - last_texcoord) * 255.0;
    }

    void render_material(MaterialShaderOutput m) {
        
        // Compute material properties
        vec3 normal = normalize(m.normal);
        vec3 diffuse_color = saturate(m.basecolor) * saturate(1 - m.metallic);
        vec3 specular_color = saturate(m.basecolor) * saturate(m.metallic) * saturate(m.specular);
        specular_color += vec3(0.02) * saturate(1 - m.metallic);
        float roughness = saturate(m.roughness);
        vec2 velocity = compute_velocity();

        gbuffer_out_0 = vec4(diffuse_color.r, diffuse_color.g, diffuse_color.b, roughness);
        gbuffer_out_1 = vec4(m.normal.x, m.normal.y, m.normal.z, specular_color.r);
        gbuffer_out_2 = vec4(velocity.x, velocity.y, specular_color.g, specular_color.b);
    }


#else // IS_GBUFFER_SHADER


    /*

    GBuffer - Unpacking

    */


    #pragma include "Includes/PositionReconstruction.inc.glsl"
    #pragma include "Includes/Structures/GBufferData.struct.glsl"


    // Utility function
    bool is_skybox(Material m, vec3 camera_pos) {
        return distance(m.position, camera_pos) > 20000.0;
    }

    float get_gbuffer_depth(GBufferData data, ivec2 coord) {
        return texelFetch(data.Depth, coord, 0).x;
    }

    float get_gbuffer_depth(GBufferData data, vec2 coord) {
        return textureLod(data.Depth, coord, 0).x;
    }

    vec3 get_gbuffer_position(GBufferData data, ivec2 coord) {
        vec2 float_coord = (coord+0.5) /  SCREEN_SIZE;
        float depth = get_gbuffer_depth(data, coord);
        return calculateSurfacePos(depth, float_coord);
    }


    vec3 get_gbuffer_normal(GBufferData data, vec2 float_coord) {
        vec3 raw_normal = textureLod(data.Data1, float_coord, 0).xyz;
        return normal_unquantization(raw_normal);
    }

    vec3 get_gbuffer_normal(GBufferData data, ivec2 coord) {
        vec3 raw_normal = texelFetch(data.Data1, coord, 0).xyz;
        return normal_unquantization(raw_normal); 
    }

    vec2 get_gbuffer_velocity(GBufferData data, ivec2 coord) {
        return texelFetch(data.Depth, coord, 0).xy / 255.0;
    }


    Material unpack_material(GBufferData data) {

        Material m;

        ivec2 coord = ivec2(gl_FragCoord.xy);

        // Compute position from depth
        m.position = get_gbuffer_position(data, coord);

        // Fetch data from data-textures
        vec4 data0 = texelFetch(data.Data0, coord, 0);
        vec4 data1 = texelFetch(data.Data1, coord, 0);
        vec4 data2 = texelFetch(data.Data2, coord, 0);

        // Unpack data
        m.diffuse = data0.xyz;
        m.roughness = max(0.001, data0.w);
        m.normal = normal_unquantization(data1.xyz);
        m.specular = vec3(data1.w, data2.zw);

        // Velocity, not unpacked yet
        // vec2 velocity = data2.xy;

        return m;
    }




#endif // IS_GBUFFER_SHADER