#version 430

#pragma include "Includes/Configuration.inc.glsl"
#pragma include "Includes/GBufferPacking.inc.glsl"


in vec2 texcoord;
out vec4 result;

uniform vec3 cameraPosition;

#pragma include "../compute_scattering.inc.glsl"

uniform writeonly imageCube DestCubemap;

uniform sampler2D DefaultSkydome;

void main() {

    // Get cubemap coordinate
    ivec2 coord = ivec2(gl_FragCoord.xy);
    int face = coord.x / 256;
    coord = coord % 256;
    vec2 local_coord = (coord / 255.0) * 2.0 - 1.0;

    vec3 coord_3d = get_cubemap_coordinate(face, local_coord);

    float horizon = coord_3d.z;

    coord_3d.z = abs(coord_3d.z);


    // vec3 scattering_result = vec3(0);
    vec3 inscattered_light = DoScattering(coord_3d * 10000000.0, coord_3d);


    vec3 sky_color = textureLod(DefaultSkydome, get_skydome_coord(coord_3d), 0).xyz;

    inscattered_light = 1.0 - exp(-0.2 * inscattered_light);

    // inscattered_light = pow(inscattered_light, vec3(1.0 / 2.2));

    inscattered_light += pow(sky_color, vec3(1.2)) * 0.5;


    if (horizon < 0.0) {
        inscattered_light *= 0.5;
    }

    imageStore(DestCubemap, ivec3(coord, face), vec4(inscattered_light, 1.0) );

    result.xyz = inscattered_light;

}