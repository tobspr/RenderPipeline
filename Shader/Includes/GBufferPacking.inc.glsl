#pragma once

#pragma include "Includes/Configuration.inc.glsl"
#pragma include "Includes/Structures/Material.struct.glsl"

#define USE_NORMAL_QUANTIZATION 0


#if defined(IS_GBUFFER_SHADER)

uniform mat4 currentViewProjMatNoJitter;

layout(location=0) out vec4 gbuffer_out_0;
layout(location=1) out vec4 gbuffer_out_1;
layout(location=2) out vec4 gbuffer_out_2;

#if USE_NORMAL_QUANTIZATION
// Normal Quantization as described in the cryengine paper:
// http://advances.realtimerendering.com/s2010/Kaplanyan-CryEngine3(SIGGRAPH%202010%20Advanced%20RealTime%20Rendering%20Course).pdf
// Page 39 to 49
uniform sampler2D NormalQuantizationTex;

vec3 normal_quantization(vec3 normal)
{
    
    normal = normalize(normal);
    // return normal * 0.5 + 0.5;
    vec3 normal_abs = abs(normal.xyz);
    float max_comp = max(normal_abs.x, max(normal_abs.y, normal_abs.z));
    vec2 cube_coord = normal_abs.z < max_comp ?
        (normal_abs.y < max_comp ? normal.yz : normal.xz) : normal.xy;

    cube_coord /= max_comp;    

    ivec2 face_offs = ivec2( (cube_coord + 1.0));
    cube_coord = cube_coord + 1;

    // look-up fitting length and scale the normal to get the best fit
    float fitting_scale = texture(NormalQuantizationTex, cube_coord).x;

    return normal * fitting_scale * 0.5 + 0.5;
    // return vec3(min_scale);
}


#else

vec3 normal_quantization(vec3 normal) {
    return normalize(normal);
} 

#endif

void render_material(Material m) {

    m.normal = normal_quantization(m.normal);
    m.diffuse = saturate(m.diffuse);
    
    // Compute velocity
    vec4 last_proj_pos = vOutput.last_proj_position;
    vec2 last_texcoord = fma(last_proj_pos.xy / last_proj_pos.w, vec2(0.5), vec2(0.5));

    // vec2 curr_texcoord = vec2( (gl_FragCoord.xy) / vec2(WINDOW_WIDTH, WINDOW_HEIGHT));

    vec4 curr_proj_pos = currentViewProjMatNoJitter * vec4(vOutput.position, 1);
    vec2 curr_texcoord = fma(curr_proj_pos.xy / curr_proj_pos.w, vec2(0.5), vec2(0.5));

    vec2 velocity = (curr_texcoord - last_texcoord) * 255.0;

    gbuffer_out_0 = vec4(m.diffuse, m.roughness);
    gbuffer_out_1 = vec4(m.normal, m.metallic);
    gbuffer_out_2 = vec4(m.specular, velocity.x, velocity.y, 1);

}


#else

#pragma include "Includes/PositionReconstruction.inc.glsl"

Material unpack_material(sampler2D GBufferDepth, sampler2D GBuffer0, sampler2D GBuffer1, sampler2D GBuffer2) {  
    Material m;

    ivec2 coord = ivec2(gl_FragCoord.xy);
    vec2 coordF = vec2(coord+0.5) / vec2(WINDOW_WIDTH, WINDOW_HEIGHT);

    // Compute position from depth
    float depth = texelFetch(GBufferDepth, coord, 0).x;
    m.position = calculateSurfacePos(depth, coordF);

    vec4 data0 = texelFetch(GBuffer0, coord, 0);
    vec4 data1 = texelFetch(GBuffer1, coord, 0);
    vec4 data2 = texelFetch(GBuffer2, coord, 0);

    m.diffuse = data0.xyz;
    m.roughness = max(0.05, data0.w);

    #if USE_NORMAL_QUANTIZATION
        m.normal = normalize(data1.xyz * 2 - 1);
    #else
        m.normal = normalize(data1.xyz);
    #endif

    // m.normal = normalize(data1.xyz);
    m.metallic = data1.w;
    m.specular = max(0.01, data2.x);

    return m;
}

vec3 get_gbuffer_normal(sampler2D GBuffer1, vec2 texcoord) {
    #if USE_NORMAL_QUANTIZATION
        return normalize( fma(texture(GBuffer1, texcoord).xyz, vec3(2.0),  vec3(-1.0)) );
    #else
        return normalize(texture(GBuffer1, texcoord).xyz);
    #endif
}

vec3 get_gbuffer_normal(sampler2D GBuffer1, ivec2 coord) {
    #if USE_NORMAL_QUANTIZATION
        return normalize( fma(texelFetch(GBuffer1, coord, 0).xyz, vec3(2.0),  vec3(-1.0)) );
    #else
        // return normalize(texelFetch(GBuffer1, coord, 0).xyz);
        return (texelFetch(GBuffer1, coord, 0).xyz);
    #endif
}


vec2 get_velocity(sampler2D GBuffer2, ivec2 texcoord) {
    return texelFetch(GBuffer2, texcoord, 0).yz / 255.0;
}

bool is_skybox(Material m, vec3 camera_pos) {
    return distance(m.position, camera_pos) > 20000.0;
}

#endif 