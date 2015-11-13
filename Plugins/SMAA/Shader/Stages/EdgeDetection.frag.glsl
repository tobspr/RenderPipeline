#version 400


#pragma include "../SMAAWrap.inc.glsl"

uniform sampler2D GBufferDepth;
uniform sampler2D ShadedScene;
uniform sampler2D SRGBSource;
uniform sampler2D PredicationSource;

in vec2 texcoord;
out vec4 result;

void main() {

    // "Vertex shader"
    vec4 offset[3];
    SMAAEdgeDetectionVS(texcoord, offset);

    // Actual Fragment shader
    result = vec4(0);

    #if SMAA_PREDICATION
        // result.xy = SMAADepthEdgeDetectionPS(texcoord, offset, GBufferDepth);
        result.xy = SMAAColorEdgeDetectionPS(texcoord, offset, SRGBSource, PredicationSource);
    #else
        // result.xy = SMAADepthEdgeDetectionPS(texcoord, offset, GBufferDepth);
        result.xy = SMAAColorEdgeDetectionPS(texcoord, offset, SRGBSource);
    #endif

}