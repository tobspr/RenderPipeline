#version 410
#pragma file "Skybox.fragment"

#pragma include "Includes/VertexOutput.include"

// Input from the vertex shader
layout(location=0) in VertexOutput vOutput;

// This is required for the materials
#pragma include "Includes/MaterialPacking.include"

// Also this enables us to compute the tangent in
// the fragment shader
#pragma include "Includes/TangentFromDDX.include"

void main() {
    // Create a material to store the properties on
    Material m;
    m.baseColor = vec3(0);
    m.roughness = 1.0;
    m.specular = 0.0;
    m.metallic = 0.0;
    m.normal = vOutput.normalWorld;
    m.position = vOutput.positionWorld;
    m.translucency = 0.0;
    
    renderMaterial(m);
}
