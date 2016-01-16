#version 430

#pragma include "Includes/Configuration.inc.glsl"
#pragma include "Includes/ImportanceSampling.inc.glsl"
#pragma include "Includes/PoissonDisk.inc.glsl"
#pragma include "Includes/BRDF.inc.glsl"

#pragma optionNV (unroll all)

uniform int currentMip;
uniform samplerCube SourceTex;
uniform writeonly imageCube RESTRICT DestMipmap;

void main() {

    // Get cubemap coordinate
    int texsize = imageSize(DestMipmap).x;
    ivec2 coord = ivec2(gl_FragCoord.xy);

    ivec2 clamped_coord; int face;
    vec3 n = texcoord_to_cubemap(texsize, coord, clamped_coord, face);

    float sample_roughness = 1e-6 + currentMip * 0.1;
    // sample_roughness = sample_roughness * sample_roughness;

    vec3 accum = vec3(0);

    vec3 tangent, binormal;
    find_arbitrary_tangent(n, tangent, binormal);
    // -------- Importance Sampling ----------

    const int num_samples = 32;
    float accum_weights = 0.0;

    for (int i = 0; i < num_samples; ++i) {
        vec2 Xi = hammersley(i, num_samples);
        vec3 h = importance_sample_ggx(Xi, sample_roughness);
        h = normalize(h.x * tangent + h.y * binormal + h.z * n);

        // Reconstruct light vector
        vec3 l = -reflect(n, h);

        // float NxH = max(0, dot(n, h));
        float NxL = max(0, dot(n, l));
        // float LxH = max(0, dot(h, l));

        float weight = NxL;
        accum += textureLod(SourceTex, l, currentMip).xyz * weight;
        accum_weights += weight;
    }

    // Energy conservation
    accum /= max(0.01, accum_weights);
    
    imageStore(DestMipmap, ivec3(clamped_coord, face), vec4(accum, 1.0));
}
