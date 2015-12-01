#pragma once

#pragma include "Includes/Configuration.inc.glsl"
#pragma include "Includes/Structures/Material.struct.glsl"



#pragma include "Includes/NormalPacking.inc.glsl"


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
        vec2 packed_normal = pack_normal_octrahedron(normal);

        // Clamp BaseColor, but only for negative values, we allow values > 1.0
        vec3 basecolor = max(vec3(0), m.basecolor);

        // Clamp properties like specular and metallic, which have to be in the
        // 0 ... 1 range
        float specular = saturate(m.specular);
        float metallic = saturate(m.metallic);
        float roughness = clamp(m.roughness, 0.001, 1.0);

        // Optional: Use squared roughness as proposed by Disney
        roughness *= roughness;

        vec2 velocity = compute_velocity();

        float UNUSED_0 = 0.0;
        float UNUSED_1 = 0.0;

        gbuffer_out_0 = vec4(basecolor.r, basecolor.g, basecolor.b, roughness);
        gbuffer_out_1 = vec4(packed_normal.x, packed_normal.y, metallic, specular);
        gbuffer_out_2 = vec4(velocity.x, velocity.y, UNUSED_0, UNUSED_1);
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
        // vec3 raw_normal = textureLod(data.Data1, float_coord, 0).xyz;
        // return normal_unquantization(raw_normal);
        vec2 packed_normal = textureLod(data.Data1, float_coord, 0).xy;
        return unpack_normal_octrahedron(packed_normal);
    }

    vec3 get_gbuffer_normal(GBufferData data, ivec2 coord) {
        // vec3 raw_normal = texelFetch(data.Data1, coord, 0).xyz;
        // return normal_unquantization(raw_normal); 
        vec2 packed_normal = texelFetch(data.Data1, coord, 0).xy;
        return unpack_normal_octrahedron(packed_normal);
    }

    vec2 get_gbuffer_velocity(GBufferData data, ivec2 coord) {
        return texelFetch(data.Data2, coord, 0).xy / 255.0;
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

        m.basecolor = data0.xyz;
        m.roughness = data0.w;
        m.normal = unpack_normal_octrahedron(data1.xy);
        m.metallic = data1.z;
        m.specular = data1.w;

        float UNUSED_0 = data2.z;
        float UNUSED_1 = data2.w;

        // Velocity, not unpacked here
        vec2 velocity = data2.xy;

        return m;
    }




#endif // IS_GBUFFER_SHADER
