#version 430

#pragma include "Includes/Configuration.inc.glsl"
#pragma include "Includes/ImportanceSampling.inc.glsl"
#pragma include "Includes/PoissonDisk.inc.glsl"
#pragma include "Includes/BRDF.inc.glsl"

#pragma optionNV (unroll all)

uniform int currentMip;
uniform samplerCube SourceTex;
uniform writeonly imageCube RESTRICT DestMipmap;

out vec4 result;

void main() {

    // Get cubemap coordinate
    int texsize = imageSize(DestMipmap).x;
    ivec2 coord = ivec2(gl_FragCoord.xy);

    ivec2 clamped_coord; int face;
    vec3 n = texcoord_to_cubemap(texsize, coord, clamped_coord, face);

    float sample_roughness = 0.03 + currentMip * 0.09;

    vec3 accum = vec3(0);

    // -------- Importance Sampling ----------

    const int num_samples = 64;
    float accum_weights = 0.0;

    for (int i = 0; i < num_samples; ++i) {
        vec2 Xi = poisson_disk_2D_64[i] * sample_roughness;

        #if 1
        vec3 tangent, binormal;
        find_arbitrary_tangent(n, tangent, binormal);

        // Compute halfway vector
        vec3 h = normalize(Xi.x * tangent + Xi.y * binormal + n);
       
        #else

        vec3 h = ImportanceSampleGGX(Xi, sample_roughness, n);

        #endif

        // Reconstruct light vector
        vec3 l = -reflect(n, h);

        // Get lighting brdf
        float NxH = max(0, dot(n, h));
        // float NxL = max(0, dot(n, l));
        // float LxH = max(0, dot(h, l));

        // Visibility has to get multiplied later on
        float distribution = brdf_distribution(NxH, sample_roughness);
        // float fresnel = brdf_fresnel(LxH, sample_roughness);
        const float fresnel = 1.0; // No noticeable difference, runs faster tho
        float weight = distribution * fresnel;

        vec3 fval = textureLod(SourceTex, l, currentMip).xyz;
        accum += fval * weight;
        accum_weights += weight;
    }

    // Energy conservation
    accum /= max(0.01, accum_weights);
    
    result.xyz = accum;
    result.w = 1.0;

    imageStore(DestMipmap, ivec3(clamped_coord, face), vec4(accum, 1.0));
}