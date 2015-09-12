#version 430

#pragma include "Includes/Configuration.include"
#pragma include "Includes/Structures/VertexOutput.struct"
#pragma include "Includes/Structures/Material.struct"
#pragma include "Includes/ForwardPlusShading.include"

layout(location=0) in VertexOutput vOutput;

uniform sampler2D p3d_Texture0;

void main() {

    vec4 diffuseSample = texture(p3d_Texture0, vOutput.texcoord);

    Material m;
    m.diffuse = diffuseSample.xyz;
    m.normal = vOutput.normal;
    m.position = vOutput.position;
    m.metallic = 1.0;
    m.specular = 1.0;
    m.roughness = 1.0;

    process_and_render_material(m);
}

