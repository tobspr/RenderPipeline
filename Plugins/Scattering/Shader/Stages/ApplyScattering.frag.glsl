#version 400

#pragma include "Includes/Configuration.inc.glsl"
#pragma include "Includes/GBufferPacking.inc.glsl"

uniform sampler2D ShadedScene;
uniform sampler2D DefaultSkydome;

uniform sampler2D GBufferDepth;
uniform sampler2D GBuffer0;
uniform sampler2D GBuffer1;
uniform sampler2D GBuffer2;

in vec2 texcoord;
out vec4 result;

uniform vec3 cameraPosition;

#pragma include "../compute_scattering.inc.glsl"


void main() {

    Material m = unpack_material(GBufferDepth, GBuffer0, GBuffer1, GBuffer2);
        
    vec3 view_vector = normalize(m.position - cameraPosition);
    vec3 scattering_result = vec3(0);
    vec3 inscattered_light = DoScattering(m.position, view_vector);

    if (is_skybox(m, cameraPosition) && m.position.z > 0.0) {
        vec3 cloud_color = textureLod(DefaultSkydome, get_skydome_coord(view_vector), 0).xyz;
        // scattering_result = 1.0 - exp(-0.2 * inscattered_light);
        inscattered_light += pow(cloud_color, vec3(1.2)) * 0.4 * 0.1 * sunIntensity;

    } else {
    }
        // scattering_result = 1.0 - exp(-1.0*inscattered_light);
    // scattering_result = inscattered_light;
    scattering_result = inscattered_light;

    result = texture(ShadedScene, texcoord);
    result.xyz += scattering_result;
}