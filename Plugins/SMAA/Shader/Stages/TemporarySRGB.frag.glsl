#version 400

#pragma include "Includes/Configuration.inc.glsl"
#pragma include "Includes/Tonemapping.inc.glsl"
#pragma include "Includes/GBufferPacking.inc.glsl"


uniform sampler2D ShadedScene;
uniform sampler2D GBufferDepth;
uniform sampler2D GBuffer1;
uniform vec3 cameraPosition;

in vec2 texcoord;
out vec4 result;
out vec4 result_predication;

void main() {
    ivec2 coord = ivec2(gl_FragCoord.xy);
    vec4 scene_data = texelFetch(ShadedScene, coord, 0);
    vec3 nrm = get_gbuffer_normal(GBuffer1, coord);

    scene_data.xyz = Tonemap_Uncharted2(scene_data.xyz);
    scene_data.w = 1.0;
    result = scene_data;
    result_predication = vec4(nrm * 0.5 + 0.5, 0);
}
