#version 430

// Filters the generated noisy diffuse cubemap to make it smooth

#pragma include "Includes/Configuration.inc.glsl"
#pragma include "Includes/PoissonDisk.inc.glsl"

#pragma optionNV (unroll all)

uniform samplerCube SourceTex;
uniform writeonly imageCube RESTRICT DestMipmap;
uniform int currentMip;

void main() {

    // Get cubemap coordinate
    int texsize = textureSize(SourceTex, currentMip).x;
    ivec2 coord = ivec2(gl_FragCoord.xy);

    ivec2 clamped_coord; int face;
    vec3 n = texcoord_to_cubemap(texsize, coord, clamped_coord, face);

    vec3 accum = vec3(0.0);

    // Get tangent and binormal
    vec3 tangent, binormal;
    find_arbitrary_tangent(n, tangent, binormal);

    const float filter_radius = 0.00 + currentMip * 0.05;
    const int num_samples = 64;
    for (int i = 0; i < num_samples; ++i) {
        vec2 offset = poisson_disk_2D_64[i];
        vec3 sample_vec = normalize(n +
            filter_radius * offset.x * tangent +
            filter_radius * offset.y * binormal);
        accum += textureLod(SourceTex, sample_vec, currentMip).xyz;
    }
    accum /= num_samples;
    imageStore(DestMipmap, ivec3(clamped_coord, face), vec4(accum, 1.0));
}
