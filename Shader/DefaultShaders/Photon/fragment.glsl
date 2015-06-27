#version 410

#pragma include "Includes/Structures/VertexOutput.struct"

// Input from the vertex shader
layout(location=0) in VertexOutput vOutput;

// This is required for the materials
#pragma include "Includes/MaterialPacking.include"
#pragma include "Includes/CommonFunctions.include"

void main() {

    // Create a material to store the properties on
    Material m = getDefaultMaterial();

    // Store the properties
    m.baseColor = vOutput.materialDiffuse.xyz;
    m.roughness = 1.0;
    m.specular = 0.0;
    m.metallic = 0.0;
    m.normal = vOutput.normalWorld;
    m.position = vOutput.positionWorld;

    // Write the material to the G-Buffer
    renderMaterial(m);
}