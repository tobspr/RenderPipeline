#version 400

#pragma include "Includes/Configuration.inc.glsl"
#pragma include "../SMAAWrap.inc.glsl"

uniform sampler2D EdgeTex;
uniform sampler2D AreaTex;
uniform sampler2D SearchTex;

uniform int JitterIndex;

out vec4 result;

void main() {

    vec2 texcoord = get_texcoord();

    // "Vertex shader"
    vec4 offset[3];
    vec2 pixcoord;
    SMAABlendingWeightCalculationVS(texcoord, pixcoord, offset);

    #if GET_SETTING(SMAA, use_reprojection)
        vec4 subsampleIndices = JitterIndex == 0 ? vec4(1, 1, 1, 0) : vec4(2, 2, 2, 0);
    #else
        vec4 subsampleIndices = vec4(0);
    #endif

    if (textureLod(EdgeTex, texcoord, 0).w < 0.5) discard;

    // Actual Fragment shader
    result = SMAABlendingWeightCalculationPS(texcoord, pixcoord, offset, EdgeTex, AreaTex, SearchTex, subsampleIndices);
    
}