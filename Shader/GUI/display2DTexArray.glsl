#version 400

in vec2 texcoord;
out vec4 result;

uniform sampler2DArray p3d_Texture0;

void main() {
    ivec2 coord = ivec2(texcoord * textureSize(p3d_Texture0, 0).xy);
    vec4 colorSum = vec4(0);
    int numLevels = textureSize(p3d_Texture0, 0).z;
    for (int i = 0; i < numLevels; i++) {
        colorSum += texelFetch(p3d_Texture0, ivec3(coord, i), 0);
    }
    colorSum /= float(numLevels);
    result = colorSum;
    result.w = 1.0;
}

