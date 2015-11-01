#version 400


#pragma include "../SMAAWrap.inc.glsl"

uniform sampler2D BlendTex;
uniform sampler2D ColorCorrectedScene;

in vec2 texcoord;
out vec4 result;

void main() {

    // "Vertex shader"
    vec4 offset;
    SMAANeighborhoodBlendingVS(texcoord, offset);

    // Actual Fragment shader
    #if SMAA_REPROJECTION
        result = SMAANeighborhoodBlendingPS(texcoord, offset, ColorCorrectedScene, BlendTex, velocityTex);
    #else
        result = SMAANeighborhoodBlendingPS(texcoord, offset, ColorCorrectedScene, BlendTex);
    #endif
}