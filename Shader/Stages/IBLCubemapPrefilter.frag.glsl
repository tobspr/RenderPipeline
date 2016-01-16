#version 430

#pragma include "Includes/Configuration.inc.glsl"
#pragma include "Includes/PoissonDisk.inc.glsl"

#pragma optionNV (unroll all)

uniform samplerCube SourceCubemap;
uniform writeonly imageCube RESTRICT DestCubemap;

out vec4 result;

void main() {

    const int texsize = 10;


    ivec2 coord = ivec2(gl_FragCoord.xy);
    ivec2 clamped_coord; int face;
    vec3 n = texcoord_to_cubemap(texsize, coord, clamped_coord, face);

    vec3 accum = vec3(0.0);

    // Get tangent and binormal
    vec3 tangent, binormal;
    find_arbitrary_tangent(n, tangent, binormal);

    const float filter_radius = 0.4;
    const int num_samples = 16;
    for (int i = 0; i < num_samples; ++i) {
        vec2 offset = poisson_disk_2D_16[i];
        vec3 sample_vec = normalize(n +
            filter_radius * offset.x * tangent +
            filter_radius * offset.y * binormal);
        accum += textureLod(SourceCubemap, sample_vec, 0).xyz;
    }
    accum /= num_samples;

    imageStore(DestCubemap, ivec3(clamped_coord, face), vec4(accum, 1.0));
}
