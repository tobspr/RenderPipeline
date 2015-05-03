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

// out vec4 color0;

#pragma include "Includes/Transparency.include"
#pragma include "Includes/PositionReconstruction.include"

uniform vec3 cameraPosition;


void main() {

    TransparentMaterial tm = getDefaultTransparentMaterial();
    tm.color = vOutput.materialDiffuse.xyz;
    tm.alpha = 0.4;
    tm.normal = normalize(vOutput.normalWorld);
    tm.depth = distance(cameraPosition, vOutput.positionWorld) / CAMERA_FAR;
    tm.materialType = 0;
    renderTransparentMaterial(tm);
}