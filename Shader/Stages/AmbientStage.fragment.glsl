#version 400

#pragma include "Includes/Configuration.include"
#pragma include "Includes/GBufferPacking.include"

in vec2 texcoord;
uniform sampler2D ShadedScene;
uniform sampler2D GBufferDepth;
uniform sampler2D GBuffer0;
uniform sampler2D GBuffer1;
uniform sampler2D GBuffer2;

out vec4 result;



void main() {




    Material m = unpack_material(GBufferDepth, GBuffer0, GBuffer1, GBuffer2);

    vec4 ambient = vec4(0);

    ambient.xyz = m.diffuse * 0.05;

    result = texture(ShadedScene, texcoord) + ambient;
}