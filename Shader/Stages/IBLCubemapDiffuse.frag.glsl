#version 430

#pragma include "Includes/Configuration.inc.glsl"
#pragma include "Includes/ImportanceSampling.inc.glsl"
#pragma include "Includes/ImportanceSampling/ImportanceSampleLambert.inc.glsl"
#pragma include "Includes/PoissonDisk.inc.glsl"

#pragma optionNV (unroll all)

uniform samplerCube SourceCubemap;
uniform writeonly imageCube RESTRICT DestCubemap;

out vec4 result;

void main() {

    const int texsize = 32;
    const int sample_count = 128;

    ivec2 coord = ivec2(gl_FragCoord.xy);
    ivec2 clamped_coord; int face;
    vec3 n = texcoord_to_cubemap(texsize, coord, clamped_coord, face);


    vec3 accum = vec3(0);

    for (int i = 0; i < sample_count; ++i)
    {
        vec3 offset = importance_sample_brdf_128[i];
        vec3 sample_vec = tangent_to_world(n, offset);
        sample_vec = normalize(sample_vec);
        accum += textureLod(SourceCubemap, sample_vec, 0).xyz;
    }

    accum /= sample_count;
    // accum /= M_PI; // Lambert

    imageStore(DestCubemap, ivec3(clamped_coord, face), vec4(accum, 1) );
    result = vec4(accum, 1);
}
