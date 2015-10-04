#version 400

#pragma include "Includes/Configuration.inc.glsl"
#pragma include "Includes/GBufferPacking.inc.glsl"

in vec2 texcoord;
uniform sampler2D ShadedScene;
uniform sampler2D GBufferDepth;
uniform sampler2D GBuffer0;
uniform sampler2D GBuffer1;
uniform sampler2D GBuffer2;

uniform samplerCube DefaultEnvmap;
uniform vec3 cameraPosition;

out vec4 result;



void main() {

    Material m = unpack_material(GBufferDepth, GBuffer0, GBuffer1, GBuffer2);


    vec3 viewVector = normalize(m.position - cameraPosition);
    vec4 ambient = vec4(0);

    ambient.xyz = m.diffuse * 0.05 + abs(m.normal.x) * 0.05;

    vec3 reflection_coord = reflect(viewVector, m.normal);
    vec3 env_coord = fix_cubemap_coord(reflection_coord);
    float env_mipmap = 5.0;
    vec3 env_default_color = textureLod(DefaultEnvmap, env_coord, env_mipmap).xyz;

    ambient.xyz = env_default_color * 0.2;

    result = texture(ShadedScene, texcoord) + ambient;
}