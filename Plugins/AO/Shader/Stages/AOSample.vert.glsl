#version 400

#pragma include "Includes/Configuration.inc.glsl"

in vec4 p3d_Vertex;
out vec2 texcoord;
flat out int instance;

void main() {
    int x = gl_InstanceID % 2;
    int y = gl_InstanceID / 2;

    CONST_ARRAY float rotations[4] = float[4](180, 270, 90, 0);

    // Rotate the vertices because we use oversized triangles
    float rotation = rotations[gl_InstanceID] / 180.0 * M_PI;

    vec2 pcoord = rotate(p3d_Vertex.xz, rotation);
    texcoord = fma(pcoord, vec2(0.5), vec2(0.5));
    pcoord.xy = pcoord.xy * 0.5 - 0.5 + 1.0 * vec2(x, y);

    instance = gl_InstanceID;
    gl_Position = vec4(pcoord, 0, 1);
}
