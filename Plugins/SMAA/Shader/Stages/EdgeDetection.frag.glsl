#version 400


#pragma include "../SMAAWrap.inc.glsl"

uniform sampler2D GBufferDepth;
uniform sampler2D ShadedScene;

in vec2 texcoord;
out vec4 result;

void main() {

    // "Vertex shader"
    vec4 offset[3];
    SMAAEdgeDetectionVS(texcoord, offset);

    // Actual Fragment shader
    result = vec4(0);

    #if SMAA_PREDICATION
        result.xy = SMAAColorEdgeDetectionPS(texcoord, offset, ShadedScene, GBufferDepth);
    #else
        result.xy = SMAAColorEdgeDetectionPS(texcoord, offset, ShadedScene);
    #endif

}