#pragma once

#pragma include "Includes/Configuration.inc.glsl"
#pragma include "Includes/Structures/Material.struct.glsl"

#if defined(IS_GBUFFER_SHADER)

uniform sampler2D NormalQuantizationTex;

layout(location=0) out vec4 gbuffer_out_0;
layout(location=1) out vec4 gbuffer_out_1;
layout(location=2) out vec4 gbuffer_out_2;


// Normal Quantization as described in the cryengine paper:
// http://advances.realtimerendering.com/s2010/Kaplanyan-CryEngine3(SIGGRAPH%202010%20Advanced%20RealTime%20Rendering%20Course).pdf
// Page 39 to 49

vec3 normal_quantization(vec3 normal)
{
    normal = normalize(normal);
    vec3 normalUnsigned = abs(normal.rgb);
    float maxComponent = max(normalUnsigned.x, max(normalUnsigned.y, normalUnsigned.z));
    vec2 cubeCoord = normalUnsigned.z < maxComponent ?
        (normalUnsigned.y < maxComponent ? normalUnsigned.yz : normalUnsigned.xz) : normalUnsigned.xy;
    cubeCoord = cubeCoord.x < cubeCoord.y ? cubeCoord.yx : cubeCoord.xy;
    cubeCoord.y /= cubeCoord.x;
    normal /= maxComponent;

    // look-up fitting length and scale the normal to get the best fit
    float fittingScale = texture(NormalQuantizationTex, cubeCoord).x;

    // scale the normal to get the best fit
    // normal *= fittingScale;
    // normal = normal * 0.5 + 0.5;
    return normal;
}



void render_material(Material m) {

    m.normal = normal_quantization(m.normal);
    m.diffuse = saturate(m.diffuse);
    gbuffer_out_0 = vec4(m.diffuse, m.roughness);
    gbuffer_out_1 = vec4(m.normal, m.metallic);
    gbuffer_out_2 = vec4(m.specular, 0, 0, 1);
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
    m.roughness = max(0.01, data0.w);
    // m.normal = normalize(data1.xyz * 2 - 1);
    m.normal = normalize(data1.xyz);
    m.metallic = data1.w;
    m.specular = max(0.01, data2.x);

    return m;
}

vec3 get_gbuffer_normal(sampler2D GBuffer1, vec2 texcoord) {
    // return normalize(texture(GBuffer1, texcoord).xyz * 2 - 1);
    return normalize(texture(GBuffer1, texcoord).xyz);
}

#endif