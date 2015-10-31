#version 430

%DEFINES%

#define IS_GBUFFER_SHADER 1

#pragma include "Includes/Configuration.inc.glsl"
#pragma include "Includes/Structures/VertexOutput.struct.glsl"
#pragma include "Includes/Structures/Material.struct.glsl"

%INCLUDES%

layout(location=0) in VertexOutput vOutput;

// Late include of the gbuffer packing since it needs the vOutput
#pragma include "Includes/GBufferPacking.inc.glsl"

uniform sampler2D p3d_Texture0;

uniform float roughness;
uniform float metallic;
uniform float specular;

%INOUT%

void main() {

    vec4 diffuseSample = texture(p3d_Texture0, vOutput.texcoord);

    Material m;
    m.diffuse = diffuseSample.xyz;
    m.normal = vOutput.normal;
    m.position = vOutput.position;
    m.metallic = metallic;
    m.specular = specular;
    m.roughness = roughness;
    
    if (specular > 0.4) {
        m.diffuse = vec3(0.5);
    }

    %MATERIAL%

    render_material(m);
}
