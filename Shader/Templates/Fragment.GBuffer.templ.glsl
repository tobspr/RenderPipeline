#version 430

%DEFINES%

#define IS_GBUFFER_SHADER 1

#define USE_MAIN_SCENE_DATA
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

void main() {

    // Fetch texture data
    float sampled_specular  = texture(p3d_Texture2, vOutput.texcoord).x;
    float sampled_roughness = texture(p3d_Texture3, vOutput.texcoord).x;

    #if OPT_ALPHA_TESTING
        // Do binary alpha testing, but weight it based on the distance to the
        // camera. This prevents alpha tested objects getting too thin when
        // viewed from a high distance.
        // TODO: Might want to make the alpha testing distance configurable
        vec4 sampled_diffuse = texture(p3d_Texture0, vOutput.texcoord);
        float dist_to_camera = distance(MainSceneData.camera_pos, vOutput.position);
        float alpha_factor = mix(0.99, 0.1, saturate(dist_to_camera / 20.0) );
        if (sampled_diffuse.w < alpha_factor) discard;
    #else
        // In case we don't do alpha testing, we don't need the w-component, so
        // don't fetch it. In practice, most GPU's will still load the w component
        // and discard it, but it surely can't hurt.
        vec3 sampled_diffuse = texture(p3d_Texture0, vOutput.texcoord).xyz;
    #endif

    #ifdef OPT_NORMAL_MAPPING
        // Perform normal mapping if enabled
        vec3 sampled_normal = texture(p3d_Texture1, vOutput.texcoord).xyz;
        vec3 detail_normal = unpack_texture_normal(sampled_normal);
        vec3 merged_normal = apply_normal_map(vOutput.normal, detail_normal, vOutput.bumpmap_factor * 0);
    #else
        // Otherwise just use the per-vertex normal
        vec3 merged_normal = vOutput.normal;
    #endif

    // Generate the material output
    MaterialShaderOutput m;
    m.basecolor = vOutput.material_color * sampled_diffuse.xyz;
    m.normal = merged_normal;
    m.metallic = vOutput.material_metallic;
    m.specular = vOutput.material_specular * sampled_specular;
    m.roughness = vOutput.material_roughness * sampled_roughness;
    m.translucency = 0.0;

    %MATERIAL%

    render_material(m);
}
