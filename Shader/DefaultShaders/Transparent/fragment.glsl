#version 410

#pragma include "Includes/Configuration.include"
#pragma include "Includes/Structures/VertexOutput.struct"


#extension GL_EXT_shader_image_load_store : enable

// Input from the vertex shader
layout(location=0) in VertexOutput vOutput;

// Transparency bufers
layout (r32ui) coherent uniform uimage2D pixelCountBuffer;
layout (r32ui) coherent uniform uimage2D listHeadBuffer;
layout (r32i) coherent uniform iimage2D spinLockBuffer;
layout (rgba32ui) coherent uniform uimageBuffer materialDataBuffer;

#pragma include "Includes/Transparency.include"

uniform vec3 cameraPosition;

void main() {

    TransparentMaterial tm = getDefaultTransparentMaterial();
    tm.color = vOutput.materialDiffuse.xyz;
    tm.alpha = 0.4;
    tm.normal = normalize(vOutput.normalWorld);
    tm.roughness = 0.5;
    tm.specular = 0.5;
    tm.metallic = 0.0;
    renderTransparentMaterial(tm);
}