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


void main() {

    TransparentMaterial tm = getDefaultTransparentMaterial();
    tm.color = vec3(0.6, 0.6, 0.6);
    tm.alpha = 0.5;
    tm.normal = normalize(vOutput.normalWorld);
    tm.depth = gl_FragCoord.z;
    tm.materialType = 0;


    // tm.normal = vec3( abs(vOutput.positionWorld.x) / 8.0, 0, 1);


    renderTransparentMaterial(tm);
}