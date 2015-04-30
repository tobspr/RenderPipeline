#version 410


#pragma include "Includes/VertexOutput.include"

// Input from the vertex shader
layout(location=0) in VertexOutput vOutput;

// This is required for the materials
#pragma include "Includes/Material.include"
#pragma include "Includes/MaterialPacking.include"

// Also this enables us to compute the tangent in
// the fragment shader
#pragma include "Includes/TangentFromDDX.include"

uniform sampler2D skytex;

void main() {
    // Create a material to store the properties on
    Material m = getDefaultMaterial();

    vec2 skycoord = clamp(vOutput.texcoord * vec2(1,2) + vec2(0, 0.03), vec2(0, 0.99), vec2(1, 1.9));

    m.baseColor = texture(skytex, skycoord).xyz;
    m.roughness = 1.0;
    m.specular = 0.0;
    m.metallic = 0.0;
    m.normal = vOutput.normalWorld;
    m.position = vOutput.positionWorld;
    m.translucency = 0.0;
    
    renderMaterial(m);
}
