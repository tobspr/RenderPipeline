#version 430

#pragma include "Includes/Configuration.inc.glsl"

in vec2 texcoord;
out vec4 result;

uniform int current_mip;
uniform samplerCube SourceMipmap;
uniform writeonly imageCube DestMipmap;

void main() {

    // Get cubemap coordinate
    int texsize = imageSize(DestMipmap).x;

    ivec2 coord = ivec2(gl_FragCoord.xy);
    int face = coord.x / texsize;
    ivec2 clamped_coord = coord % texsize;

    vec2 local_coord = (clamped_coord / float(texsize - 1)) * 2.0 - 1.0;
    float pixel_size = 2.0 / float(texsize);

    vec3 blurred_values = vec3(0);

    const int filter_size = 3;

    float accum = 0.01;

    for (int i = -filter_size; i <= filter_size; i++) {
        for (int j = -filter_size; j <= filter_size; j++) {

            vec3 coord_3d = get_cubemap_coordinate(face, local_coord + pixel_size * vec2(i, j));
    
            float weight = 1.0 / (0.5 + 1.0 * length(vec2(i, j)));
            blurred_values += textureLod(SourceMipmap, coord_3d, current_mip).xyz * weight;
            accum += weight;

        }
    }

    blurred_values /= accum;

    result.xyz = blurred_values;
    result.w = 1.0;

    imageStore(DestMipmap, ivec3(clamped_coord, face), vec4(blurred_values, 1.0));

}