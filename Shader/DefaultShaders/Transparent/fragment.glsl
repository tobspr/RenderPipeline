#version 400




#pragma include "Includes/Configuration.include"
#pragma include "Includes/VertexOutput.include"

#extension GL_ARB_separate_shader_objects : enable
#extension GL_EXT_shader_image_load_store : enable

// Input from the vertex shader
layout(location=0) in VertexOutput vOutput;

layout (rgba8) uniform image2DArray transparencyLayers;
layout (r32f) uniform image2DArray transparencyDepthLayers;
layout (r32i) uniform iimage2D transparencyIndices;

#pragma include "Includes/Transparency.include"


layout(location=0) out vec4 color0;
layout(location=1) out vec4 color1;
layout(location=2) out vec4 color2;
layout(location=3) out vec4 color3;

void main() {

    float lightFactor = 0.2 + saturate(dot(normalize(vOutput.normalWorld), normalize(vec3(0.2,1.2,1.6))) ) * 0.5;
    // lightFactor = 1.0;
    vec3 color = vec3(0.2,0.6,1.0) * lightFactor;
    float alpha = 0.5;
    float depth = gl_FragCoord.z;
    vec2 coord = gl_FragCoord.xy;

    renderTransparentObject(color, alpha, depth, coord);
   
}