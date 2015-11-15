#version 400

#pragma include "Includes/Configuration.inc.glsl"
#pragma include "Includes/GBufferPacking.inc.glsl"
#pragma include "Includes/BRDF.inc.glsl"
#pragma include "Includes/Lights.inc.glsl"

in vec2 texcoord;
uniform sampler2D ShadedScene;
uniform sampler2D GBufferDepth;
uniform sampler2D GBuffer0;
uniform sampler2D GBuffer1;
uniform sampler2D GBuffer2;

uniform sampler2D PrefilteredBRDF;

uniform samplerCube DefaultEnvmap;
uniform vec3 cameraPosition;

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

    int num_mipmaps = get_mipmap_count(map);
    // float reflectivity = saturate(1.0 - roughness);

    // Increase mipmap at extreme roughness, linear doesn't work well there
    // reflectivity += saturate(reflectivity - 0.9) * 2.0;
    return roughness * 10.0;
    // return (num_mipmaps - reflectivity * 9.0);
}



void main() {

    ivec2 coord = ivec2(gl_FragCoord.xy);

    // Get material properties
    Material m = unpack_material(GBufferDepth, GBuffer0, GBuffer1, GBuffer2);


    // Get view vector
    vec3 view_vector = normalize(m.position - cameraPosition);


    // Store the accumulated ambient term in a variable
    vec4 ambient = vec4(0);

    #if !DEBUG_MODE

    // Skip skybox shading (TODO: Do this with stencil masking)
    if (!is_skybox(m, cameraPosition)) {


        // Get reflection directory
        vec3 reflected_dir = reflect(view_vector, m.normal);

        // Get environment coordinate, cubemaps have a different coordinate system
        vec3 env_coord = fix_cubemap_coord(reflected_dir);

        // Compute angle between normal and view vector
        float NxV = abs(dot(m.normal, view_vector));

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
            env_amb = textureLod(ScatteringCubemap, m.normal, 5).xyz;

        #endif

        // Get prefiltered BRDF
        vec2 prefilter_brdf = textureLod(PrefilteredBRDF, vec2(1-m.roughness, NxV), 0).xy;
        vec3 prefilter_color = m.diffuse * prefilter_brdf.x + prefilter_brdf.y;


        // Different terms for metallic and diffuse objects:

        // Metallic specular term: Just plain reflections
        vec3 env_metallic = m.diffuse;

        // Diffuse specular term: Prefiltered BRDF. TODO: Do we really need the´0.2?
        vec3 env_diffuse = prefilter_color * 0.2;

        // Mix diffuse and metallic specular term based on material metallic,
        // and multiply it by the material specular
        vec3 env_factor = mix(env_diffuse, env_metallic, m.metallic) * m.specular;

        // Diffuse ambient term, weight it by 0 for metallics
        vec3 diffuse_ambient = vec3(0.02) * m.diffuse * (1.0 - m.metallic);

        // Specular ambeint term
        vec3 specular_ambient = env_factor * env_default_color;

        // Add diffuse and specular ambient term
        ambient.xyz += diffuse_ambient + specular_ambient;

        // Add "fake" irradiance term
        ambient.xyz += env_amb * 0.05 * m.diffuse * (1.0 - m.metallic);


        #if HAVE_PLUGIN(AO)

            // Sample precomputed occlusion and multiply the ambient term with it
            float occlusion = texelFetch(AmbientOcclusion, coord, 0).w;
            ambient *= saturate(pow(occlusion, 3.0));

        #endif

        // ambient.xyz = vec3(specular_ambient);

    }

    #endif

    ambient.w = 0.0;


    #if DEBUG_MODE
        #if MODE_ACTIVE(OCCLUSION)
            float occlusion = texelFetch(AmbientOcclusion, coord, 0).w;
            ambient = vec4(pow(occlusion, 1.5));
        #endif
    #endif

    result = texture(ShadedScene, texcoord) * 1 + ambient * 1;
}