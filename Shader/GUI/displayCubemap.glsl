#version 400

#pragma include "Includes/CommonFunctions.inc.glsl"

in vec2 texcoord;
out vec4 result;

uniform samplerCube p3d_Texture0;
uniform int mipmap;

void main() {
    vec2 tlocal = mod(texcoord, 1.0);
    int face = int(texcoord.x * 6.0);

    vec3 dir = get_cubemap_coordinate(face, tlocal);

    result = textureLod(p3d_Texture0, vec3(dir), mipmap);
    result.w = 1.0;
}