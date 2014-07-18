#version 400

#include "Includes/VertexOutput.include"

// Input from the vertex shader
in VertexOutput vOutput;

// This is required for the materials
#include "Includes/MaterialPacking.include"

void main() {

    // Create a material to store the properties on
    Material m;
    vec3 normal = normalize(vOutput.normalWorld);

    m.metallic = 0.0;
    m.roughness = 0.0;
    m.specular = 0.0;
    m.baseColor = vec3(0);
    m.position = vOutput.positionWorld;
    m.normal = normal;

    // Pack material and output to the render targets
    renderMaterial(m);
}