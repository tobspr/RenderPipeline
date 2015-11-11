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
uniform sampler2D p3d_Texture1;
uniform sampler2D p3d_Texture2;
uniform sampler2D p3d_Texture3;

%INOUT%

void main() {

    vec4 sampled_diffuse   = texture(p3d_Texture0, vOutput.texcoord);
    vec4 sampled_normal    = texture(p3d_Texture1, vOutput.texcoord);
    vec4 sampled_specular  = texture(p3d_Texture2, vOutput.texcoord);
    vec4 sampled_roughness = texture(p3d_Texture3, vOutput.texcoord);


    Material m;
    m.diffuse = vOutput.material_color * sampled_diffuse.xyz;
    m.normal = vOutput.normal;
    m.position = vOutput.position;
    m.metallic = vOutput.material_metallic;
    m.specular = vOutput.material_specular * sampled_specular.x;
    m.roughness = vOutput.material_roughness * sampled_roughness.x;
    
    %MATERIAL%

    render_material(m);
}
