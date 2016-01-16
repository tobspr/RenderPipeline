#version 430

// Filters the input cubemap using importance sampling

#pragma include "Includes/Configuration.inc.glsl"
#pragma include "Includes/ImportanceSampling.inc.glsl"
#pragma include "Includes/PoissonDisk.inc.glsl"

// #pragma optionNV (unroll all)

uniform samplerCube SourceCubemap;
uniform writeonly imageCube RESTRICT DestCubemap;
uniform int cubeSize;

out vec4 result;

void main() {
    const int sample_count = 64;

    ivec2 coord = ivec2(gl_FragCoord.xy);
    ivec2 clamped_coord; int face;
    vec3 n = texcoord_to_cubemap(cubeSize, coord, clamped_coord, face);

    // Convert normal to spherical coordinates
    float theta, phi;
    vector_to_spherical(n, theta, phi);

    float search_angle = degree_to_radians(90.0);

    vec3 accum = vec3(0);
    float weights = 1e-5;

    // Get tangent and binormal
    vec3 tangent, binormal;
    find_arbitrary_tangent(n, tangent, binormal);

    // Add noise by rotating tangent and bitangent
    const int noise_size = 4;
    int noise_id = int(coord.x) % noise_size + (int(coord.y) % noise_size) * noise_size;
    float rotation = noise_id / float(noise_size * noise_size) * TWO_PI;
    float sin_r = sin(rotation);
    float cos_r = cos(rotation);

    for (int i = 0; i < sample_count; ++i)
    {
        vec2 xi = hammersley(i, sample_count);
        xi = rotate(xi, cos_r, sin_r);
        vec3 offset = importance_sample_lambert(xi, n);
        offset = normalize(tangent * offset.x + binormal * offset.y + n * offset.z);
        offset = faceforward(offset, offset, -n);

        float weight = saturate(dot(offset, n));
        accum += textureLod(SourceCubemap, offset, 0).xyz * weight;
        weights += weight;
    }

    accum /= weights;

    imageStore(DestCubemap, ivec3(clamped_coord, face), vec4(accum, 1) );
    result = vec4(accum, 1);
}
