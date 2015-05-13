#version 410

#pragma include "Includes/Structures/VertexOutput.struct"


// Input from the vertex shader
layout(location=0) in VertexOutput vOutput;

// Texture Samplers
uniform sampler2D p3d_Texture0;

// This is required for the materials
#pragma include "Includes/MaterialPacking.include"


void main() {

    // Create a material to store the properties on
    Material m = getDefaultMaterial();

    // Sample the diffuse color
    vec4 sampledDiffuse = texture(p3d_Texture0, vOutput.texcoord);
    
    // Alpha test
    if (sampledDiffuse.a < 0.5) discard;

    // Store the properties
    m.baseColor = vec3(10) * vOutput.materialDiffuse.xyz;
    m.roughness = 1.0;
    m.specular = 0.0;
    m.metallic = 0.0;
    m.normal = vOutput.normalWorld;
    m.position = vOutput.positionWorld;
    renderMaterial(m);
}