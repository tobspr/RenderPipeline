#version 400

#pragma include "render_pipeline_base.inc.glsl"
uniform sampler2D ShadedScene;
out vec4 color;

void main() {
    vec2 texcoord = get_texcoord();
    color.xyz = texture(ShadedScene, texcoord).xyz;
    color.w  = dot(color.xyz, vec3(0.299, 0.587, 0.114));
}
