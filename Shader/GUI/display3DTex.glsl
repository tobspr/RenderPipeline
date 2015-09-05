#version 400

in vec2 texcoord;
out vec4 result;

uniform sampler3D p3d_Texture0;

void main() {
    vec4 colorSum = vec4(0);
    int numLevels = textureSize(p3d_Texture0, 0).z;
    for (int i = 0; i < numLevels; i++) {
        colorSum += texture(p3d_Texture0, vec3(texcoord, i / float(numLevels)));
    }
    colorSum /= float(numLevels);
    result = colorSum;
    result.w = 1.0;

}