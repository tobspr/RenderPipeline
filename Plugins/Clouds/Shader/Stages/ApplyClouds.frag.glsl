#version 400

#pragma include "Includes/Configuration.inc.glsl"

uniform sampler2D CloudsTex;
uniform sampler2D ShadedScene;
out vec4 result;

void main() {
    vec2 texcoord = get_texcoord();
    vec4 scene_color = textureLod(ShadedScene, texcoord, 0);
    vec4 cloud_color = textureLod(CloudsTex, texcoord, 0);
    result = mix(scene_color, cloud_color, cloud_color.w);
    result.w = scene_color.w;
}
