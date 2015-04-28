#version 410
#pragma file "Skybox.fragment"

#include "Includes/VertexOutput.include"

// Input from the vertex shader
layout(location=0) in VertexOutput vOutput;

// This is required for the materials
#include "Includes/MaterialPacking.include"

// Also this enables us to compute the tangent in
// the fragment shader
#include "Includes/TangentFromDDX.include"

uniform sampler2D skytex;

void main() {
    // Create a material to store the properties on
    Material m;

    vec2 skycoord = vOutput.texcoord * vec2(1,2) + vec2(0, 0.0);

    m.baseColor = texture(skytex, skycoord).xyz;
    m.roughness = 1.0;
    m.specular = 0.0;
    m.metallic = 0.0;
    m.normal = vOutput.normalWorld;
    m.position = vOutput.positionWorld;
    


    renderMaterial(m);
}