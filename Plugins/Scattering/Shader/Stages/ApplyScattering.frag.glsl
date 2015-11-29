#version 400

#pragma include "Includes/Configuration.inc.glsl"
#pragma include "Includes/GBuffer.inc.glsl"

uniform sampler2D ShadedScene;
uniform sampler2D DefaultSkydome;

uniform GBufferData GBuffer;

in vec2 texcoord;
out vec4 result;

uniform vec3 cameraPosition;

#pragma include "../compute_scattering.inc.glsl"


void main() {

    Material m = unpack_material(GBuffer);
        
    vec3 view_vector = normalize(m.position - cameraPosition);
    vec3 scattering_result = vec3(0);
    float fog_factor = 0.0;
    vec3 inscattered_light = DoScattering(m.position, view_vector, fog_factor);

    if (is_skybox(m, cameraPosition) && view_vector.z > - cameraPosition.z * 0.015) {
        vec3 cloud_color = textureLod(DefaultSkydome, get_skydome_coord(view_vector), 0).xyz;
        inscattered_light += pow(cloud_color.y, 3.5) * sunIntensity * 0.8 * inscattered_light;

    }
    
    scattering_result = inscattered_light;

    result = texture(ShadedScene, texcoord);
    result.xyz = mix(result.xyz, scattering_result, fog_factor);
    result.w = fog_factor;
}
