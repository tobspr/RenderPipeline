#version 430

layout (local_size_x = 16, local_size_y = 16) in;


uniform sampler2D directionX;
uniform sampler2D directionY;
uniform sampler2D directionZ;

uniform writeonly image2D destination;

void main() {
    ivec2 texelCoords = ivec2(gl_GlobalInvocationID.xy);

    vec4 resultX = texelFetch(directionX, texelCoords, 0);
    vec4 resultY = texelFetch(directionY, texelCoords, 0);
    vec4 resultZ = texelFetch(directionZ, texelCoords, 0);
    vec4 resultCombined = resultX + resultY + resultZ;
    resultCombined /= max(1.0, resultCombined.w);

    imageStore(destination, texelCoords, resultCombined);
}
