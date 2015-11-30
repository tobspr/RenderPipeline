#version 430

#pragma include "Includes/Configuration.inc.glsl"

in vec2 texcoord;
out vec4 result;

uniform vec3 cameraPosition;

uniform writeonly imageCube DestCubemap;
uniform sampler2D DefaultSkydome;

#pragma include "../ScatteringMethod.inc.glsl"

void main() {

    // Get cubemap coordinate
    int texsize = imageSize(DestCubemap).x;
    ivec2 coord = ivec2(gl_FragCoord.xy);

    // Get cubemap direction
    ivec2 clamped_coord; int face;
    vec3 direction = texcoord_to_cubemap(texsize, coord, clamped_coord, face);

    // Store horizon
    float horizon = direction.z;
    direction.z = abs(direction.z);
    float fog_factor = 0.0;

    // Get inscattered light
    vec3 inscattered_light = DoScattering(direction * 1e10, direction, fog_factor);


    if (horizon > 0.0) {
        // Clouds
        vec3 cloud_color = textureLod(DefaultSkydome, get_skydome_coord(direction), 0).xyz;
         inscattered_light += pow(cloud_color.y, 2.5) * TimeOfDay.Scattering.sun_intensity * 0.1;
    } else {
        // Ground reflectance
        inscattered_light *= saturate(1+0.9*horizon) * 0.2;
        inscattered_light += pow(vec3(102, 82, 50) * (1.0 / 255.0), vec3(1.0 / 1.2)) * saturate(-horizon + 0.2) * 0.2 * TimeOfDay.Scattering.sun_intensity * 0.1;
    }

    imageStore(DestCubemap, ivec3(clamped_coord, face), vec4(inscattered_light, 1.0) );
    result.xyz = inscattered_light;
}