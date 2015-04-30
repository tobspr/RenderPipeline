#version 400




#pragma include "Includes/Configuration.include"
#pragma include "Includes/VertexOutput.include"

#extension GL_ARB_separate_shader_objects : enable
#extension GL_EXT_shader_image_load_store : enable

// Input from the vertex shader
layout(location=0) in VertexOutput vOutput;

// layout (rgba8) uniform image2DArray transparencyLayers;
// layout (r32f) uniform image2DArray transparencyDepthLayers;
layout (r32ui) coherent uniform uimage2D pixelCountBuffer;
layout (r32ui) coherent uniform uimage2D listHeadBuffer;
layout (r32i) coherent uniform iimage2D spinLockBuffer;
layout (rgba32ui) coherent uniform uimageBuffer materialDataBuffer;


#pragma include "Includes/Transparency.include"


layout(location=0) out vec4 color0;
layout(location=1) out vec4 color1;
layout(location=2) out vec4 color2;
layout(location=3) out vec4 color3;

void main() {

    TransparentMaterial tm = getDefaultTransparentMaterial();
    tm.color = vec3(1.0, 0.6, 0.2);
    tm.alpha = 0.5;
    tm.normal = normalize(vOutput.normalWorld);
    tm.depth = gl_FragCoord.z;
    tm.materialType = 0;



    renderTransparentMaterial(tm);
}