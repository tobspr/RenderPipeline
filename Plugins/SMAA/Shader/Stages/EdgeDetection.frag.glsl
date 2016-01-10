#version 420

#define USE_MAIN_SCENE_DATA
#pragma include "Includes/Configuration.inc.glsl"

#pragma include "../SMAAWrap.inc.glsl"
#pragma include "Includes/GBuffer.inc.glsl"

uniform GBufferData GBuffer;
uniform sampler2D ShadedScene;
uniform sampler2D SRGBSource;
uniform sampler2D PredicationSource;
out vec4 result;

void main() {

    vec2 texcoord = get_texcoord();

    // "Vertex shader"
    vec4 offset[3];
    SMAAEdgeDetectionVS(texcoord, offset);

    // Actual Fragment shader
    result = vec4(0);

    #if SMAA_PREDICATION
        // result.xy = SMAADepthEdgeDetectionPS(texcoord, offset, GBuffer.Depth);
        result.xy = SMAAColorEdgeDetectionPS(texcoord, offset, SRGBSource, PredicationSource);
    #else
        // result.xy = SMAADepthEdgeDetectionPS(texcoord, offset, GBuffer.Depth);
        result.xy = SMAAColorEdgeDetectionPS(texcoord, offset, SRGBSource);
    #endif

    result.w = 1.0;
}