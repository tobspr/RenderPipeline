#version 420

#pragma include "Includes/Configuration.include"
#pragma include "Includes/Structures/VertexOutput.struct"

// Input from the vertex shader
layout(location=0) in VertexOutput vOutput;

#pragma include "Includes/Transparency.include"

void main() {

    // Create the default transparent material and assign its material properties.
    TransparentMaterial tm = getDefaultTransparentMaterial();
    tm.color = vOutput.materialDiffuse.xyz;
    tm.alpha = 0.4;
    tm.normal = normalize(vOutput.normalWorld);
    tm.roughness = vOutput.materialSpecular.z;
    tm.specular = vOutput.materialSpecular.x;
    tm.metallic = vOutput.materialSpecular.y;


    // Finally render the material
    renderTransparentMaterial(tm);
}

