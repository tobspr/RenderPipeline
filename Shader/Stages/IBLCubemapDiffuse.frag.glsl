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

    const int texsize = 64;
    const int sample_count = 16;

    ivec2 coord = ivec2(gl_FragCoord.xy);
    ivec2 clamped_coord; int face;
    vec3 n = texcoord_to_cubemap(texsize, coord, clamped_coord, face);
    float noise_factor = 0.0;
    vec3 accum = vec3(0);

    // Get tangent and binormal
    vec3 tangent, binormal;
    find_arbitrary_tangent(n, tangent, binormal);

    // Add noise by rotating tangent and bitangent
    int noise_id = int(coord.x) % 3 + (int(coord.y) % 3) * 3;
    float rotation = noise_id / 9.0 * TWO_PI;
    float sin_r = sin(rotation);
    float cos_r = cos(rotation);

    for (int i = 0; i < sample_count; ++i)
    {
        vec3 offset = importance_sample_brdf_64[i];
        offset.xy = vec2(
            offset.x * cos_r - offset.y * sin_r,
            offset.x * sin_r + offset.y * cos_r
        );
        vec3 sample_vec = tangent * offset.x + binormal * offset.y + n * offset.z;
        accum += textureLod(SourceCubemap, sample_vec, 0).xyz;
    }

    accum /= sample_count;

    imageStore(DestCubemap, ivec3(clamped_coord, face), vec4(accum, 1) );
    result = vec4(accum, 1);
}
