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
#pragma include "includes/color_spaces.inc.glsl"

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

#if HAVE_PLUGIN(sslr)
    uniform sampler2D SSLRSpecular;
#endif

out vec4 result;

float get_mipmap_for_roughness(samplerCube map, float roughness) {
    return roughness * 7.0;
}

float compute_specular_occlusion(float NxV, float occlusion, float roughness) {
    // return occlusion;
    return saturate(pow(NxV + occlusion, roughness) - 1 + occlusion);
}

// From: http://www.frostbite.com/wp-content/uploads/2014/11/course_notes_moving_frostbite_to_pbr.pdf
vec3 compute_bloom_luminance(vec3 bloom_color, float bloom_ec, float current_ev) {
    // currentEV is the value calculated at the previous frame
    float bloom_ev = current_ev + bloom_ec;
    // convert to luminance
    return bloom_color * pow(2, bloom_ev - 3);
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
    #if 0
        float mipmap_bias = abs(dFdx(m.roughness)) + abs(dFdy(m.roughness));
        mipmap_bias += saturate(pow(1.0 - NxV, 15.0));
        mipmap_bias *= 4.0;
    #else
        float mipmap_bias = 0.0;
    #endif

    // Get mipmap offset for the material roughness
    float env_mipmap = get_mipmap_for_roughness(DefaultEnvmap, m.roughness) + mipmap_bias;

    // Sample default environment map
    vec3 ibl_specular = textureLod(DefaultEnvmap, reflected_dir, env_mipmap).xyz * 0.2;
    // Get cheap irradiance by sampling low levels of the environment map
    int ibl_diffuse_mip = get_mipmap_count(DefaultEnvmap) - 5;
    vec3 ibl_diffuse = textureLod(DefaultEnvmap, m.normal, ibl_diffuse_mip).xyz * 0.2;

    // Scattering specific code
    #if HAVE_PLUGIN(scattering)

        float scat_mipmap = m.shading_model == SHADING_MODEL_CLEARCOAT ?
            CLEARCOAT_ROUGHNESS : get_specular_mipmap(m);
        scat_mipmap += mipmap_bias;

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

    #if HAVE_PLUGIN(sslr)
        vec4 sslr_spec = textureLod(SSLRSpecular, texcoord, 0);
        ibl_specular = ibl_specular * (1 - sslr_spec.w) + sslr_spec.xyz;
    #endif


    vec3 material_f0 = get_material_f0(m);
    vec3 specular_ambient = vec3(0);

    // Pre-Integrated environment BRDF
    vec2 env_brdf = textureLod(PrefilteredBRDF, vec2(NxV, m.roughness), 0).xy;

    if (m.shading_model == SHADING_MODEL_CLEARCOAT) {
        // Sample prefiltered scattering cubemap
        vec2 env_brdf_coat = textureLod(PrefilteredBRDF, vec2(NxV, CLEARCOAT_ROUGHNESS), 0).xy;
        float fresnel_coat = saturate(CLEARCOAT_SPECULAR * env_brdf_coat.x + env_brdf_coat.y);

        #if HAVE_PLUGIN(scattering)
            vec3 ibl_specular_base = textureLod(ScatteringIBLSpecular, reflected_dir, get_specular_mipmap(m) + mipmap_bias).xyz;
        #else
            vec3 ibl_specular_base = textureLod(DefaultEnvmap, reflected_dir, get_mipmap_for_roughness(DefaultEnvmap, m.roughness) + mipmap_bias).xyz;
        #endif

        specular_ambient = fresnel_coat * ibl_specular;

        // Make sure we don't apply a bright sky cubemap on dark spots
        float specular_clip =  saturate(15.0 * get_luminance(ibl_specular));
        specular_clip = 1 - fresnel_coat; // XXX: Find a better solution for the clip factor
        specular_ambient += material_f0 * ibl_specular_base * specular_clip;

    } else {
        specular_ambient = (material_f0 * env_brdf.x + env_brdf.y) * ibl_specular;
    }

    // Diffuse ambient term
    vec3 diffuse_ambient = ibl_diffuse * m.basecolor * (1-m.metallic) / M_PI;


    #if HAVE_PLUGIN(ao)
        // Sample precomputed occlusion and multiply the ambient term with it
        float occlusion = textureLod(AmbientOcclusion, texcoord, 0).x;
        float specular_occlusion = compute_specular_occlusion(NxV, occlusion, m.roughness);
    #else
        const float occlusion = 1.0;
        const float specular_occlusion = 1.0;
    #endif


    // Add diffuse and specular ambient term
    ambient = diffuse_ambient * occlusion + specular_ambient * specular_occlusion;

    #endif

    // Emissive materials
    if (m.shading_model == SHADING_MODEL_EMISSIVE) {
        ambient = m.basecolor * 4000.0;
    }

    // TODO:
    // For emissive, use: compute_bloom_luminance()

    #if DEBUG_MODE
        #if MODE_ACTIVE(OCCLUSION)
            result = textureLod(AmbientOcclusion, texcoord, 0).xxxx;
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
