#version 420

#define USE_MAIN_SCENE_DATA
#pragma include "Includes/Configuration.inc.glsl"
#pragma include "Includes/GBuffer.inc.glsl"
#pragma include "Includes/BRDF.inc.glsl"
#pragma include "Includes/Lights.inc.glsl"

in vec2 texcoord;
uniform sampler2D ShadedScene;
uniform GBufferData GBuffer;
uniform sampler2D PrefilteredBRDF;

uniform samplerCube DefaultEnvmap;

#if HAVE_PLUGIN(Scattering)
    uniform samplerCube ScatteringCubemap;
#endif

#if HAVE_PLUGIN(AO)
    uniform sampler2D AmbientOcclusion;
#endif

out vec4 result;

float get_mipmap_for_roughness(samplerCube map, float roughness) {

    // We compute roughness in the shader as:    
    // float sample_roughness = current_mip * 0.1;
    // So current_mip is sample_roughness / 0.1

    roughness = sqrt(roughness);

    int num_mipmaps = get_mipmap_count(map);
    float reflectivity = saturate(1.0 - roughness);

    // Increase mipmap at extreme roughness, linear doesn't work well there
    // reflectivity += (0.1 - min(0.1, roughness) ) / 0.1 * 20.0;
    // return sqrt(roughness) * 8.0;
    return (num_mipmaps - reflectivity * 9.0);
}



void main() {

    ivec2 coord = ivec2(gl_FragCoord.xy);

    // Get material properties
    Material m = unpack_material(GBuffer);

    // Get view vector
    vec3 view_vector = normalize(MainSceneData.camera_pos - m.position);

    // Store the accumulated ambient term in a variable
    vec3 ambient = vec3(0);

    #if !DEBUG_MODE

    // Skip skybox shading (TODO: Do this with stencil masking)
    if (!is_skybox(m, MainSceneData.camera_pos)) {

        // Get reflection directory
        vec3 reflected_dir = reflect(-view_vector, m.normal);

        // Get environment coordinate, cubemaps have a different coordinate system
        vec3 env_coord = fix_cubemap_coord(reflected_dir);

        // Compute angle between normal and view vector
        float NxV = max(1e-5, dot(m.normal, view_vector));

        // OPTIONAL: Increase mipmap level at grazing angles to decrease aliasing
        float mipmap_bias = saturate(pow(1.0 - NxV, 5.0)) * 3.0;
        mipmap_bias = 0.0;

        // Get mipmap offset for the material roughness
        float env_mipmap = get_mipmap_for_roughness(DefaultEnvmap, m.roughness) + mipmap_bias;
        
        // Sample default environment map
        vec3 env_default_color = textureLod(DefaultEnvmap, env_coord, env_mipmap).xyz;

        // Get cheap irradiance by sampling low levels of the environment map
        int env_amb_mip = get_mipmap_count(DefaultEnvmap) - 5;
        vec3 env_amb = textureLod(DefaultEnvmap, m.normal, env_amb_mip).xyz;

        // Scattering specific code
        #if HAVE_PLUGIN(Scattering)

            // Get scattering mipmap
            float scat_mipmap = get_mipmap_for_roughness(ScatteringCubemap, m.roughness) + mipmap_bias;

            // Sample prefiltered scattering cubemap
            vec3 env_scattering_color = textureLod(ScatteringCubemap, reflected_dir, scat_mipmap).xyz;
            env_default_color = env_scattering_color;

            // Cheap irradiance
            env_amb = textureLod(ScatteringCubemap, m.normal, 4.5).xyz;

        #endif
    
        // Pre-Integrated environment BRDF
        vec2 env_brdf = textureLod(PrefilteredBRDF, vec2(NxV, m.roughness), 0).xy;
        vec3 specular_nonmetallic = vec3(env_brdf.y + 0.09 * env_brdf.x);
        specular_nonmetallic *= m.specular;

        // Metallic specular is pretty simple
        vec3 specular_metallic = m.basecolor;

        // Weight specular metallic and non-metallic terms
        vec3 specular_ambient = mix(specular_nonmetallic, specular_metallic, m.metallic) * env_default_color;

        // Diffuse ambient term
        vec3 diffuse_ambient = env_amb * m.basecolor * (1-m.metallic) / M_PI;

        // Add diffuse and specular ambient term
        ambient = diffuse_ambient + specular_ambient;

        // Reduce ambient for translucent materials
        BRANCH_TRANSLUCENCY(m)
            ambient *= saturate(1.2 - m.translucency);
        END_BRANCH_TRANSLUCENCY()

        #if HAVE_PLUGIN(AO)

            // Sample precomputed occlusion and multiply the ambient term with it
            float occlusion = texelFetch(AmbientOcclusion, coord, 0).w;
            ambient *= saturate(pow(occlusion, 3.0));

        #endif

    } else {

        // Optionally just display the environment texture
        // ambient = textureLod(DefaultEnvmap,  fix_cubemap_coord(-view_vector), 0).xyz;

    }

    #endif

    #if DEBUG_MODE
        #if MODE_ACTIVE(OCCLUSION)
            float occlusion = texelFetch(AmbientOcclusion, coord, 0).w;
            result = vec4(pow(occlusion, 3.0));
            return;
        #endif
    #endif

    vec4 scene_color = textureLod(ShadedScene, texcoord, 0);

    #if HAVE_PLUGIN(Scattering)
        // Scattering stores the fog factor in the w-component of the scene color.
        // So reduce ambient in the fog
        ambient *= (1.0 - scene_color.w);
    #endif

    result = scene_color * 1 + vec4(ambient, 1) * 1;

}
