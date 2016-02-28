/**
 *
 * RenderPipeline
 *
 * Copyright (c) 2014-2016 tobspr <tobias.springer1@gmail.com>
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 * THE SOFTWARE.
 *
 */

#version 420

#define USE_MAIN_SCENE_DATA
#pragma include "render_pipeline_base.inc.glsl"
#pragma include "includes/gbuffer.inc.glsl"
#pragma include "includes/brdf.inc.glsl"
#pragma include "includes/lights.inc.glsl"

uniform sampler2D ShadedScene;
uniform GBufferData GBuffer;
uniform sampler2D PrefilteredBRDF;

uniform samplerCube DefaultEnvmap;

#if HAVE_PLUGIN(scattering)
    uniform samplerCube ScatteringIBLDiffuse;
    uniform samplerCube ScatteringIBLSpecular;
#endif

#if HAVE_PLUGIN(ao)
    uniform sampler2D AmbientOcclusion;
#endif

#if HAVE_PLUGIN(vxgi)
    uniform sampler2D VXGISpecular;
    uniform sampler2D VXGIDiffuse;
#endif

#if HAVE_PLUGIN(env_probes)
    uniform sampler2D EnvmapAmbientDiff;
    uniform sampler2D EnvmapAmbientSpec;
#endif

out vec4 result;

float get_mipmap_for_roughness(samplerCube map, float roughness) {
    return roughness * 7.0;
}

void main() {

    vec2 texcoord = get_texcoord();

    // Get material properties
    Material m = unpack_material(GBuffer);

    // Get view vector
    vec3 view_vector = normalize(m.position - MainSceneData.camera_pos);

    // Store the accumulated ambient term in a variable
    vec3 ambient = vec3(0);

    #if !DEBUG_MODE

    // Skip skybox shading
    if (is_skybox(m)) {
        result = textureLod(ShadedScene, texcoord, 0);
        return;
    }

    // Get reflection directory
    vec3 reflected_dir = get_reflection_vector(m, view_vector);

    // Compute angle between normal and view vector
    float NxV = max(1e-5, -dot(m.normal, view_vector));

    // OPTIONAL: Increase mipmap level at grazing angles to decrease aliasing
    // float mipmap_bias = saturate(pow(1.0 - NxV, 5.0)) * 3.0;
    float mipmap_bias = 0.0;

    // Get mipmap offset for the material roughness
    float env_mipmap = get_mipmap_for_roughness(DefaultEnvmap, m.roughness) + mipmap_bias;

    // Sample default environment map
    vec3 ibl_specular = textureLod(DefaultEnvmap, reflected_dir, env_mipmap).xyz * 0.2;
    // Get cheap irradiance by sampling low levels of the environment map
    int ibl_diffuse_mip = get_mipmap_count(DefaultEnvmap) - 5;
    vec3 ibl_diffuse = textureLod(DefaultEnvmap, m.normal, ibl_diffuse_mip).xyz * 0.2;

    // Scattering specific code
    #if HAVE_PLUGIN(scattering)

        float scat_mipmap = get_specular_mipmap(m);

        // Sample prefiltered scattering cubemap
        ibl_specular = textureLod(ScatteringIBLSpecular, reflected_dir, scat_mipmap).xyz;

        // Diffuse IBL
        ibl_diffuse = texture(ScatteringIBLDiffuse, m.normal).xyz;
    #endif

    #if HAVE_PLUGIN(vxgi)
        ibl_specular = texture(VXGISpecular, texcoord).xyz;
        ibl_diffuse = texture(VXGIDiffuse, texcoord).xyz;
    #endif


    #if HAVE_PLUGIN(env_probes)
        // Mix environment maps
        vec4 probe_spec = textureLod(EnvmapAmbientSpec, texcoord, 0);
        vec4 probe_diff = textureLod(EnvmapAmbientDiff, texcoord, 0);
        ibl_specular = ibl_specular * (1 - probe_spec.w) + probe_spec.xyz;
        ibl_diffuse = ibl_diffuse * (1 - probe_diff.w) + probe_diff.xyz;
    #endif

    // Pre-Integrated environment BRDF
    // X-Component denotes the fresnel term
    // Y-Component denotes f0 factor
    vec2 env_brdf = textureLod(PrefilteredBRDF, vec2(NxV, m.roughness), 0).xy;

    vec3 material_f0 = get_material_f0(m);
    vec3 specular_ambient = (material_f0 * env_brdf.x + env_brdf.y) * ibl_specular;

    // Diffuse ambient term
    // TODO: lambertian brdf doesn't look well?
    vec3 diffuse_ambient = ibl_diffuse * m.basecolor * (1-m.metallic);

    // Add diffuse and specular ambient term
    ambient = diffuse_ambient + specular_ambient;

    #endif

    // Reduce ambient for translucent materials
    BRANCH_TRANSLUCENCY(m)
        ambient *= saturate(1.2 - m.translucency);
    END_BRANCH_TRANSLUCENCY()

    #if HAVE_PLUGIN(ao)

        // Sample precomputed occlusion and multiply the ambient term with it
        float occlusion = textureLod(AmbientOcclusion, texcoord, 0).w;

        #if HAVE_PLUGIN(vxgi)
            // When using VXGI *and* AO, reduce ao term because VXGI already
            // has an ao term
            ambient *= saturate(pow(occlusion, 1.5));
        #else
            ambient *= saturate(pow(occlusion, 3.0));
        #endif

    #endif

    // Mix emissive factor - note that we do *not* clamp the emissive factor,
    // since it can contain values much greater than 1.0
    ambient *= max(0.0, 1 - m.emissive);
    ambient += m.emissive * m.basecolor * 1000.0;


    #if DEBUG_MODE
        #if MODE_ACTIVE(OCCLUSION)
            float raw_occlusion = textureLod(AmbientOcclusion, texcoord, 0).w;
            result = vec4(pow(raw_occlusion, 3.0));
            return;
        #endif
    #endif

    vec4 scene_color = textureLod(ShadedScene, texcoord, 0);

    #if HAVE_PLUGIN(scattering)
        // Scattering stores the fog factor in the w-component of the scene color.
        // So reduce ambient in the fog
        ambient *= (1.0 - scene_color.w);
    #endif

    result = scene_color * 1 + vec4(ambient, 1) * 1;
}
