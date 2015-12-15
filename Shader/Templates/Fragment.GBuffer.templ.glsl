#version 430

%DEFINES%

#define IS_GBUFFER_SHADER 1

#pragma include "Includes/Configuration.inc.glsl"
#pragma include "Includes/Structures/VertexOutput.struct.glsl"
#pragma include "Includes/Structures/Material.struct.glsl"

%INCLUDES%

layout(location=0) in VertexOutput vOutput;

// Late include of the gbuffer packing since it needs the vOutput
#pragma include "Includes/NormalMapping.inc.glsl"
#pragma include "Includes/GBuffer.inc.glsl"

uniform sampler2D p3d_Texture0;
uniform sampler2D p3d_Texture1;
uniform sampler2D p3d_Texture2;
uniform sampler2D p3d_Texture3;

%INOUT%

uniform vec3 cameraPosition;

void main() {

    vec4 sampled_diffuse   = texture(p3d_Texture0, vOutput.texcoord);
    vec4 sampled_normal    = texture(p3d_Texture1, vOutput.texcoord);
    vec4 sampled_specular  = texture(p3d_Texture2, vOutput.texcoord);
    vec4 sampled_roughness = texture(p3d_Texture3, vOutput.texcoord);

    float dist_to_camera = distance(cameraPosition, vOutput.position);

    float alpha_factor = mix(0.99, 0.1, saturate(dist_to_camera / 20.0) );

    if (sampled_diffuse.w < alpha_factor) discard;

    vec3 detail_normal = fma(sampled_normal.xyz, vec3(2.0), vec3(-1.0));
    vec3 merged_normal = apply_normal_map(vOutput.normal, detail_normal, vOutput.bumpmap_factor);

    MaterialShaderOutput m;
    m.basecolor = vOutput.material_color * sampled_diffuse.xyz;
    m.normal = merged_normal;
    m.position = vOutput.position;
    m.metallic = vOutput.material_metallic;
    m.specular = vOutput.material_specular * sampled_specular.x;
    m.roughness = vOutput.material_roughness * sampled_roughness.x;
    m.translucency = 0.0;

    %MATERIAL%

    render_material(m);
}
