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
        vec2 packed_normal = pack_normal_octahedron(normal);
        vec2 velocity = compute_velocity();

        // Clamp BaseColor, but only for negative values, we allow values > 1.0
        vec3 basecolor = pow(max(vec3(0), m.basecolor), vec3(2.2));

        // Clamp properties like specular and metallic, which have to be in the
        // 0 ... 1 range
        float specular = saturate(m.specular);
        float metallic = saturate(m.metallic);
        float roughness = clamp(m.roughness, 0.001, 1.0);
        float translucency = saturate(m.translucency);

        // Optional: Use squared roughness as proposed by Disney
        roughness *= roughness;

        // Unused parameter
        float UNUSED_1 = 0.0;

        // Pack all values to the gbuffer
        gbuffer_out_0 = vec4(basecolor.r, basecolor.g, basecolor.b, roughness);
        gbuffer_out_1 = vec4(packed_normal.x, packed_normal.y, metallic, specular);
        gbuffer_out_2 = vec4(velocity.x, velocity.y, translucency, UNUSED_1);
    }


#else // IS_GBUFFER_SHADER


    /*

    GBuffer - Unpacking

    */

    #pragma include "Includes/PositionReconstruction.inc.glsl"
    #pragma include "Includes/Structures/GBufferData.struct.glsl"

    // Checks wheter the given material is the skybox
    bool is_skybox(Material m, vec3 camera_pos) {
        return distance(m.position, camera_pos) > 20000.0;
    }

    // Returns the depth at a given texcoord
    float get_gbuffer_depth(GBufferData data, ivec2 coord) {
        return texelFetch(data.Depth, coord, 0).x;
    }
    
    // Returns the depth at a given texcoord
    float get_gbuffer_depth(GBufferData data, vec2 coord) {
        return textureLod(data.Depth, coord, 0).x;
    }

    // Returns the world space position at a given texcoord
    vec3 get_gbuffer_position(GBufferData data, ivec2 coord) {
        vec2 float_coord = (coord+0.5) /  SCREEN_SIZE;
        float depth = get_gbuffer_depth(data, coord);
        return calculate_surface_pos(depth, float_coord);
    }

    // Returns the world space normal at a given texcoord
    vec3 get_gbuffer_normal(GBufferData data, vec2 float_coord) {
        // vec3 raw_normal = textureLod(data.Data1, float_coord, 0).xyz;
        // return normal_unquantization(raw_normal);
        vec2 packed_normal = textureLod(data.Data1, float_coord, 0).xy;
        return unpack_normal_octahedron(packed_normal);
    }

    // Returns the world space normal at a given texcoord
    vec3 get_gbuffer_normal(GBufferData data, ivec2 coord) {
        // vec3 raw_normal = texelFetch(data.Data1, coord, 0).xyz;
        // return normal_unquantization(raw_normal); 
        vec2 packed_normal = texelFetch(data.Data1, coord, 0).xy;
        return unpack_normal_octahedron(packed_normal);
    }

    // Returns the velocity at a given coordinate
    vec2 get_gbuffer_velocity(GBufferData data, ivec2 coord) {
        return texelFetch(data.Data2, coord, 0).xy / 255.0;
    }

    // Unpacks a material from the gbuffer
    Material unpack_material(GBufferData data) {
        ivec2 coord = ivec2(gl_FragCoord.xy);

        // Fetch data from data-textures
        vec4 data0 = texelFetch(data.Data0, coord, 0);
        vec4 data1 = texelFetch(data.Data1, coord, 0);
        vec4 data2 = texelFetch(data.Data2, coord, 0);

        Material m;
        m.position  = get_gbuffer_position(data, coord);
        m.basecolor = data0.xyz;
        m.roughness = max(0.002, data0.w);
        m.normal    = unpack_normal_octahedron(data1.xy);
        m.metallic  = data1.z;
        m.specular  = data1.w;
        m.translucency = data2.z;

        float UNUSED_1 = data2.w;

        // Velocity, not stored in the material properties tho
        // vec2 velocity = data2.xy;
        return m;
    }

    #ifdef USE_GBUFFER_EXTENSIONS

        /*
        
        GBuffer extensions for reading gbuffer values without having to specify
        the gbuffer.

        */

        uniform GBufferData GBuffer;
            
        // Returns the depth at a given texcoord
        float get_depth_at(vec2 coord) {
            return get_gbuffer_depth(GBuffer, coord);
        }

        // Returns the depth at a given texcoord
        float get_depth_at(ivec2 coord) {
            return get_gbuffer_depth(GBuffer, coord);
        }

        // Returns the view space position at a given texcoord
        vec3 get_view_pos_at(vec2 coord) {
            return calculate_view_pos(get_depth_at(coord), coord);
        }

        // Returns the view space position at a given texcoord
        vec3 get_view_pos_at(ivec2 coord) {
            vec2 tcoord = (coord + 0.5) / vec2(WINDOW_WIDTH, WINDOW_HEIGHT);
            return get_view_pos_at(tcoord);
        }

        // Returns the world space position at a given texcoord
        vec3 get_world_pos_at(vec2 coord) {
            return calculate_surface_pos(get_depth_at(coord), coord);
        }

        // Returns the world space position at a given texcoord
        vec3 get_world_pos_at(ivec2 coord) {
            vec2 tcoord = (coord + 0.5) / vec2(WINDOW_WIDTH, WINDOW_HEIGHT);
            return calculate_surface_pos(get_depth_at(tcoord), tcoord);
        }

        // Returns the view space normal at a given texcoord. This tries to find
        // a good fit normal, but thus is quite expensive.
        // It does not include normal mapping, since it uses the depth buffer as source.
        vec3 get_view_normal(ivec2 coord) {
            vec3 view_pos = get_view_pos_at(coord);

            // Do some work to find a good view normal
            vec3 dx_px = view_pos - get_view_pos_at(coord + ivec2(1, 0));
            vec3 dx_py = view_pos - get_view_pos_at(coord + ivec2(0, 1));

            vec3 dx_nx = get_view_pos_at(coord + ivec2(-1, 0)) - view_pos;
            vec3 dx_ny = get_view_pos_at(coord + ivec2(0, -1)) - view_pos;

            // Find the closest distance in depth
            vec3 dx_x = abs(dx_px.z) < abs(dx_nx.z) ? vec3(dx_px) : vec3(dx_nx);
            vec3 dx_y = abs(dx_py.z) < abs(dx_ny.z) ? vec3(dx_py) : vec3(dx_ny);

            return normalize(cross(dx_x, dx_y));
        }

        // Returns the view space normal at a given texcoord. This approximates
        // the normal instead of calculating it accurately, thus might produce
        // smaller artifacts at edges. However you should prefer this method
        // wherever possible. It does not include normal mapping, since it uses
        // the depth buffer as source.
        vec3 get_view_normal_approx(ivec2 coord) {
            vec3 view_pos = get_view_pos_at(coord);
            vec3 dx_x = view_pos - get_view_pos_at(coord + ivec2(1, 0));
            vec3 dx_y = view_pos - get_view_pos_at(coord + ivec2(0, 1));
            return normalize(cross(dx_x, dx_y));
        }

    #endif

#endif // IS_GBUFFER_SHADER
