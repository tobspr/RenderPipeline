/**
 * 
 * RenderPipeline
 * 
 * Copyright (c) 2014-2015 tobspr <tobias.springer1@gmail.com>
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

#pragma once

#pragma include "Includes/Configuration.inc.glsl"
#pragma include "Includes/Structures/Material.struct.glsl"
#pragma include "Includes/NormalPacking.inc.glsl"
#pragma include "Includes/BRDF.inc.glsl"

#if defined(IS_GBUFFER_SHADER)

    /*

    GBuffer Packing

    */

    layout(location=0) out vec4 gbuffer_out_0;
    layout(location=1) out vec4 gbuffer_out_1;
    layout(location=2) out vec4 gbuffer_out_2;

    vec2 compute_velocity() {
        // Compute velocity based on this and last frames mvp matrix
        vec4 last_proj_pos = vOutput.last_proj_position;
        vec2 last_texcoord = fma(last_proj_pos.xy / last_proj_pos.w, vec2(0.5), vec2(0.5));
        vec4 curr_proj_pos = MainSceneData.view_proj_mat_no_jitter * vec4(vOutput.position, 1);
        vec2 curr_texcoord = fma(curr_proj_pos.xy / curr_proj_pos.w, vec2(0.5), vec2(0.5));
        return (curr_texcoord - last_texcoord) * 255.0;
    }

    void render_material(MaterialShaderOutput m) {
        
        // Compute material properties
        vec3 normal = normalize(m.normal);
        vec2 packed_normal = pack_normal_octahedron(normal);
        vec2 velocity = compute_velocity();

        // Clamp BaseColor, but only for negative values, we allow values > 1.0
        // vec3 basecolor = pow(max(vec3(0), m.basecolor), vec3(2.2));
        vec3 basecolor = max(vec3(0), m.basecolor);

        // Clamp properties like specular and metallic, which have to be in the
        // 0 ... 1 range
        float specular = ior_to_specular(max(0.0, m.specular_ior));
        float metallic = saturate(m.metallic);
        float roughness = clamp(m.roughness, 0.005, 1.0);
        float translucency = saturate(m.translucency);


        // Optional: Use squared roughness as proposed by Disney
        roughness *= roughness;

        // Pack diffuse antialiasing factor
        float diffuse_aa = length(m.normal);

        // Pack all values to the gbuffer
        gbuffer_out_0 = vec4(basecolor.r, basecolor.g, basecolor.b, roughness);
        gbuffer_out_1 = vec4(packed_normal.x, packed_normal.y, metallic, specular);
        gbuffer_out_2 = vec4(velocity.x, velocity.y, translucency, diffuse_aa);
    }


#else // IS_GBUFFER_SHADER


    /*

    GBuffer - Unpacking

    */

    #pragma include "Includes/PositionReconstruction.inc.glsl"
    #pragma include "Includes/Structures/GBufferData.struct.glsl"

    // Checks whether the given material is the skybox
    bool is_skybox(vec3 pos, vec3 camera_pos) {
        return distance(pos, camera_pos) > 20000.0;
    }
    
    bool is_skybox(Material m, vec3 camera_pos) {
        return is_skybox(m.position, camera_pos);
    }
   
    // Returns the depth at a given texcoord
    float get_gbuffer_depth(GBufferData data, vec2 coord) {
        return textureLod(data.Depth, coord, 0).x;
    }

    // Returns the world space position at a given texcoord
    vec3 get_gbuffer_position(GBufferData data, vec2 coord) {
        float depth = get_gbuffer_depth(data, coord);
        return calculate_surface_pos(depth, coord);
    }

    // Returns the world space normal at a given texcoord
    vec3 get_gbuffer_normal(GBufferData data, vec2 coord) {
        vec2 packed_normal = textureLod(data.Data1, coord, 0).xy;
        return unpack_normal_octahedron(packed_normal);
    }
    
    // Returns the velocity at a given coordinate
    vec2 get_gbuffer_velocity(GBufferData data, vec2 coord) {
        return textureLod(data.Data2, coord, 0).xy / 255.0;
    }

    // Unpacks a material from the gbuffer
    Material unpack_material(GBufferData data) {
        vec2 fcoord = get_texcoord();

        // Fetch data from data-textures
        vec4 data0 = textureLod(data.Data0, fcoord, 0);
        vec4 data1 = textureLod(data.Data1, fcoord, 0);
        vec4 data2 = textureLod(data.Data2, fcoord, 0);

        Material m;
        m.position  = get_gbuffer_position(data, fcoord);
        m.basecolor = data0.xyz;
        m.roughness = clamp(data0.w, 0.002, 1.0);
        m.normal    = unpack_normal_octahedron(data1.xy);
        m.metallic  = data1.z * 1.001 - 0.0005;
        m.specular  = data1.w;
        m.translucency = data2.z;
        m.diffuse_aa = data2.w;

        // Velocity, not stored in the Material struct but stored in the G-Buffer
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

        // Returns the view space position at a given texcoord
        vec3 get_view_pos_at(vec2 coord) {
            return calculate_view_pos(get_depth_at(coord), coord);
        }

        // Returns the world space position at a given texcoord
        vec3 get_world_pos_at(vec2 coord) {
            return calculate_surface_pos(get_depth_at(coord), coord);
        }

        // Returns the view space normal at a given texcoord. This tries to find
        // a good fit normal, but thus is quite expensive.
        // It does not include normal mapping, since it uses the depth buffer as source.
        vec3 get_view_normal(vec2 coord) {

            // OPTIONAL: Just recover it from the world space normal.
            // This has the advantage that it does include normal mapping.
            #if 1
                vec3 world_normal = get_gbuffer_normal(GBuffer, coord);
                return world_normal_to_view(world_normal);
            #endif

            vec2 pixel_size = 1.0 / SCREEN_SIZE;
            vec3 view_pos = get_view_pos_at(coord);

            // Do some work to find a good view normal
            vec3 dx_px = view_pos - get_view_pos_at(coord + pixel_size * vec2(1, 0));
            vec3 dx_py = view_pos - get_view_pos_at(coord + pixel_size * vec2(0, 1));

            vec3 dx_nx = get_view_pos_at(coord + pixel_size * vec2(-1, 0)) - view_pos;
            vec3 dx_ny = get_view_pos_at(coord + pixel_size * vec2(0, -1)) - view_pos;

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
        vec3 get_view_normal_approx(vec2 coord) {
            vec3 view_pos = get_view_pos_at(coord);
            vec2 pixel_size = 1.0 / SCREEN_SIZE;
            vec3 dx_x = view_pos - get_view_pos_at(coord + pixel_size * vec2(1, 0));
            vec3 dx_y = view_pos - get_view_pos_at(coord + pixel_size * vec2(0, 1));
            return normalize(cross(dx_x, dx_y));
        }

    #endif

#endif // IS_GBUFFER_SHADER
