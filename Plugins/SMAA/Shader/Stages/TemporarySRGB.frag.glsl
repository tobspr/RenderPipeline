#version 400

#pragma include "Includes/Configuration.inc.glsl"

// use the extended gbuffer api
#define USE_GBUFFER_EXTENSIONS 1
#pragma include "Includes/GBuffer.inc.glsl"

uniform sampler2D ShadedScene;
uniform vec3 cameraPosition;

in vec2 texcoord;
out vec4 result;
out vec4 result_predication;

void main() {
    ivec2 coord = ivec2(gl_FragCoord.xy);
    vec3 scene_data = texelFetch(ShadedScene, coord, 0).xyz;
    vec3 nrm = get_view_normal_approx(coord);
    // Simple reinhard operator
    scene_data *= 3.0;
    scene_data = scene_data / (1.0 + scene_data);
    result = vec4(scene_data, 1);
    result_predication = vec4(fma(nrm, vec3(0.5), vec3(0.5)), 0);
}
