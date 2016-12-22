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

#version 430

// This shader applies the ambient term to the shaded scene

#define USE_GBUFFER_EXTENSIONS
#pragma include "render_pipeline_base.inc.glsl"
#pragma include "includes/gbuffer2.inc.glsl"
#pragma include "includes/brdf.inc.glsl"
#pragma include "includes/approximations.inc.glsl"
#pragma include "includes/color_spaces.inc.glsl"

uniform sampler2D ShadedScene;
uniform sampler3D PrefilteredBRDF;
uniform sampler2D PrefilteredMetalBRDF;
uniform sampler2D PrefilteredCoatBRDF;

uniform samplerCube DefaultEnvmapDiff;
uniform samplerCube DefaultEnvmapSpec;

#if HAVE_PLUGIN(scattering)
    uniform samplerCube ScatteringIBLDiffuse;
    uniform samplerCube ScatteringIBLSpecular;
    uniform sampler2D ScatteringColor;
#endif

#if HAVE_PLUGIN(ao)
    uniform sampler2D AmbientOcclusion;
#endif


#if HAVE_PLUGIN(vxgi)
    // uniform sampler2D VXGISpecular;
    uniform sampler2D VXGIDiffuse;
#endif

#if HAVE_PLUGIN(env_probes)
    uniform sampler2D EnvmapAmbientDiff;
    uniform sampler2D EnvmapAmbientSpec;
#endif

#if HAVE_PLUGIN(ssr)
    uniform sampler2D SSRSpecular;
#endif

out vec3 result;

float compute_specular_occlusion(float NxV, float occlusion, float roughness) {
    // return occlusion * 0.7 + 0.3;
    return occlusion;
    // return saturate(pow((1 - NxV) + occlusion, roughness) - 1 + occlusion);
}

// From: http://www.frostbite.com/wp-content/uploads/2014/11/course_notes_moving_frostbite_to_pbr.pdf
vec3 compute_bloom_luminance(vec3 bloom_color, float bloom_ec, float current_ev) {
    float bloom_ev = current_ev + bloom_ec;
    return bloom_color * pow(2, bloom_ev - 3);
}

vec3 get_envmap_specular(vec3 v, float mip) {
    return textureLod(DefaultEnvmapSpec, v.xzy, mip).xyz * DEFAULT_ENVMAP_BRIGHTNESS;
}

vec3 get_envmap_diffuse(vec3 n) {
    return textureLod(DefaultEnvmapDiff, n.xzy, 0).xyz * DEFAULT_ENVMAP_BRIGHTNESS;
}


void main() {
    vec2 texcoord = get_texcoord();
    Material m = gbuffer_get_material();

    vec3 view_vector = normalize(m.position - MainSceneData.camera_pos);
    vec3 ambient = vec3(0);

    vec3 scattering_color = vec3(0);

    #if HAVE_PLUGIN(scattering)
        scattering_color = textureLod(ScatteringColor, texcoord, 0).xyz;
    #endif


    // Skip skybox shading
    if (is_skybox(m)) {

        #if !REFERENCE_MODE
            result = textureLod(ShadedScene, texcoord, 0).xyz + scattering_color;

            #if !HAVE_PLUGIN(scattering)
                result = get_envmap_specular(view_vector, 0);

            #endif
        #else

            // When in reference mode, display the used environment cubemap as background
            #if USE_WHITE_ENVIRONMENT
                result = vec3(DEFAULT_ENVMAP_BRIGHTNESS);
            #else
                result = get_envmap_specular(view_vector, 0);
            #endif
        #endif

        #if !DEBUG_MODE
            return;
        #endif
    }

    float sky_ao_factor = 1.0;
    float occlusion = 1.0;

    // Sample precomputed occlusion and multiply the ambient term with it
    #if HAVE_PLUGIN(ao)
        vec2 occlusion_raw = textureLod(AmbientOcclusion, texcoord, 0).xy;

        // It is important that we pow the occlusion here, and not earlier, since
        // we are working with 8 bit targets in the ao pass
        occlusion = pow(occlusion_raw.x, 2.0);


        // SkyAO is packed into the ao texture
        #if HAVE_PLUGIN(sky_ao)
            sky_ao_factor = occlusion_raw.y;
        #endif

    #endif


    // Get reflection directory
    vec3 reflected_dir = get_reflection_vector(m, view_vector);
    float roughness = get_effective_roughness(m);

    // Compute angle between normal and view vector
    float NxV = clamp(-dot(m.normal, view_vector), 1e-5, 1.0);

    // Get mipmap offset for the material roughness
    float env_mipmap = get_mipmap_for_roughness(DefaultEnvmapSpec, roughness, NxV);

    // Sample default environment map
    vec3 ibl_specular = get_envmap_specular(reflected_dir, env_mipmap) * sky_ao_factor;
    vec3 ibl_diffuse = get_envmap_diffuse(m.normal) * sky_ao_factor;

    // Scattering specific code
    #if HAVE_PLUGIN(scattering)
        float scat_mipmap = m.shading_model == SHADING_MODEL_CLEARCOAT ?
            CLEARCOAT_ROUGHNESS : get_specular_mipmap(m);
        ibl_specular = textureLod(ScatteringIBLSpecular, reflected_dir, scat_mipmap).xyz * sky_ao_factor;
        ibl_diffuse = textureLod(ScatteringIBLDiffuse, m.normal, 0).xyz * sky_ao_factor;
    #endif

    // Blend environment maps
    #if HAVE_PLUGIN(env_probes)
        vec4 probe_spec = textureLod(EnvmapAmbientSpec, texcoord, 0);
        vec4 probe_diff = textureLod(EnvmapAmbientDiff, texcoord, 0);
        ibl_diffuse = ibl_diffuse * (1 - probe_diff.w) + probe_diff.xyz;
        ibl_specular = ibl_specular * (1 - probe_spec.w) + probe_spec.xyz;
    #endif

    // Blend VXGI on top
    #if HAVE_PLUGIN(vxgi)
        // vec4 vxgi_spec = textureLod(VXGISpecular, texcoord, 0);
        ibl_diffuse = textureLod(VXGIDiffuse, texcoord, 0).xyz;
        // ibl_specular *= ibl_diffuse;
        // ibl_specular = ibl_specular * (1 - vxgi_spec.w) + vxgi_spec.xyz;
    #endif

    // Blend screen space reflections
    #if HAVE_PLUGIN(ssr)
        vec4 ssr_spec = textureLod(SSRSpecular, texcoord, 0);

        // Fade out SSR on high roughness values
        ssr_spec *= 1.0 - saturate(m.roughness / GET_SETTING(ssr, roughness_fade));
        ssr_spec *= GET_SETTING(ssr, effect_scale);
        ibl_specular = ibl_specular * (1 - ssr_spec.w) + ssr_spec.xyz;
    #endif

    #if REFERENCE_MODE && USE_WHITE_ENVIRONMENT
        ibl_specular = vec3(DEFAULT_ENVMAP_BRIGHTNESS);
        ibl_diffuse = vec3(DEFAULT_ENVMAP_BRIGHTNESS);
    #endif

    vec3 material_f0 = get_material_f0(m);
    vec3 specular_ambient = vec3(0);

    // Pre-Integrated environment BRDF
    vec3 env_brdf = get_brdf_from_lut(PrefilteredBRDF, NxV, sqrt(roughness), m.specular_ior);

    // Exact metallic brdf lut, unused right now
    // vec3 env_brdf_metal = get_brdf_from_lut(PrefilteredMetalBRDF, NxV, roughness);

    // Diffuse and fresnel ambient term
    vec3 diffuse_ambient = ibl_diffuse * m.basecolor * (1-m.metallic);
    vec3 fresnel = env_brdf.ggg;
    diffuse_ambient *= env_brdf.r;

    // Approximate metallic fresnel
    vec3 metallic_fresnel = approx_metallic_fresnel(m, NxV);

    // Mix between normal and metallic fresnel
    fresnel = mix(fresnel, metallic_fresnel, m.metallic);

    BRANCH_CLEARCOAT(m) {
        vec3 env_brdf_coat = get_brdf_from_lut(
            PrefilteredCoatBRDF, NxV, m.linear_roughness * 1.333);

        #if HAVE_PLUGIN(scattering)
            vec3 ibl_specular_base = textureLod(
                ScatteringIBLSpecular, reflected_dir,
                get_specular_mipmap(m)).xyz * sky_ao_factor;
        #else
            vec3 ibl_specular_base = get_envmap_specular(
                reflected_dir, get_mipmap_for_roughness(DefaultEnvmapSpec, m.roughness, NxV));
        #endif

        #if REFERENCE_MODE && USE_WHITE_ENVIRONMENT
            // ibl_specular_base = vec3(1);
        #endif

        specular_ambient = env_brdf_coat.g * ibl_specular;
        specular_ambient += env_brdf_coat.r * ibl_specular_base * m.basecolor;
    } else {
        specular_ambient = fresnel * ibl_specular;
    }


    float specular_occlusion = compute_specular_occlusion(NxV, occlusion, roughness);


    // Add diffuse and specular ambient term
    ambient += diffuse_ambient * occlusion + specular_ambient * specular_occlusion;


    // Emissive materials
    #if !DEBUG_MODE
        if (m.shading_model == SHADING_MODEL_EMISSIVE) {
            // TODO: For emissive, use: compute_bloom_luminance() instead of a fixed value
            ambient = m.basecolor * EMISSIVE_SCALE;
        }
    #endif

    #if DEBUG_MODE
        #if MODE_ACTIVE(OCCLUSION) || MODE_ACTIVE(SC_OCCLUSION) || MODE_ACTIVE(CMB_OCCLUSION)
            result = vec3(occlusion);
            return;
        #endif

        #if MODE_ACTIVE(SKY_AO)
            result = vec3(sky_ao_factor);
            return;
        #endif

        #if MODE_ACTIVE(DIFFUSE_AMBIENT)
            result = (diffuse_ambient / (1 + diffuse_ambient)) * occlusion;
            return;
        #endif

        #if MODE_ACTIVE(SPECULAR_AMBIENT)
            result = (specular_ambient / (1 + specular_ambient)) * specular_occlusion;
            return;
        #endif
    #endif


    #if MODE_ACTIVE(ENVPROBE_COUNT)
        // Pass through debug modes
        result = textureLod(EnvmapAmbientDiff, texcoord, 0).xyz;
        return;
    #endif

    #if SPECIAL_MODE_ACTIVE(INVALID_NORMALS)
        // Detect invalid normals by comparing the material normal to the actual depth-based
        // normal
        vec3 depth_based_nrm = gbuffer_reconstruct_ws_normal_from_depth(texcoord);

        float diff = dot(depth_based_nrm, m.normal);
        float threshold = 0.5;
        if (diff < threshold) {
            result = vec3(10, 0, 0);
            return;
        }
    #endif


    vec3 scene_color = textureLod(ShadedScene, texcoord, 0).xyz;

    #if DEBUG_MODE
        result = scene_color;
        return;
    #endif

    result = scene_color + ambient + scattering_color;
}
