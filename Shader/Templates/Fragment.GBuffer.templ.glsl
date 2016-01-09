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


#ifndef DONT_FETCH_DEFAULT_TEXTURES
    uniform sampler2D p3d_Texture0;
    uniform sampler2D p3d_Texture1;
    uniform sampler2D p3d_Texture2;
    uniform sampler2D p3d_Texture3;

    // Only use the displacement texture if we actually need it.
    #if OPT_PARALLAX_MAPPING
        uniform sampler2D p3d_Texture4;
    #endif

#endif

%INOUT%

void main() {

    // Get texture coordinate
    #if OPT_PARALLAX_MAPPING
        // TODO: Make parallax effect controllable
        vec2 texcoord = get_parallax_texcoord(p3d_Texture4);
    #else
        vec2 texcoord = vOutput.texcoord;
    #endif

    %TEXCOORD%

    // Fetch texture data
    #ifndef DONT_FETCH_DEFAULT_TEXTURES
        float sampled_specular  = texture(p3d_Texture2, texcoord).x;
        float sampled_roughness = texture(p3d_Texture3, texcoord).x;
    #else
        float sampled_specular = 0.0;
        float sampled_roughness = 0.0;
    #endif

    #if OPT_ALPHA_TESTING
        #ifndef DONT_FETCH_DEFAULT_TEXTURES
        // Do binary alpha testing, but weight it based on the distance to the
        // camera. This prevents alpha tested objects getting too thin when
        // viewed from a high distance.
        // TODO: Might want to make the alpha testing distance configurable
            vec4 sampled_diffuse = texture(p3d_Texture0, texcoord);
            float dist_to_camera = distance(MainSceneData.camera_pos, vOutput.position);
            float alpha_factor = mix(0.99, 0.1, saturate(dist_to_camera / 20.0) );
            if (sampled_diffuse.w < alpha_factor) discard;
        #endif
    #else
        // In case we don't do alpha testing, we don't need the w-component, so
        // don't fetch it. In practice, most GPU's will still load the w component
        // and discard it, but it surely can't hurt.
        #ifndef DONT_FETCH_DEFAULT_TEXTURES
            vec3 sampled_diffuse = texture(p3d_Texture0, texcoord).xyz;
        #else
            vec3 sampled_diffuse = vec3(0);
        #endif
    #endif

    vec3 material_nrm = vOutput.normal;

    #ifdef OPT_NORMAL_MAPPING
        #ifndef DONT_FETCH_DEFAULT_TEXTURES
            {
            // Perform normal mapping if enabled
            vec3 sampled_normal = texture(p3d_Texture1, texcoord).xyz;
            vec3 detail_normal = unpack_texture_normal(sampled_normal);
            material_nrm = apply_normal_map(vOutput.normal, detail_normal, vOutput.bumpmap_factor);
            }
        #endif
    #endif

    // Generate the material output
    MaterialShaderOutput m;

    #ifndef DONT_SET_MATERIAL_PROPERTIES
        m.basecolor = vOutput.material_color * sampled_diffuse.xyz * 0.4;
        m.normal = material_nrm;
        m.metallic = vOutput.material_metallic;
        m.specular = vOutput.material_specular * sampled_specular;
        m.roughness = vOutput.material_roughness * sampled_roughness;
        m.translucency = 0.0;
    #endif

    %MATERIAL%

    render_material(m);
}
