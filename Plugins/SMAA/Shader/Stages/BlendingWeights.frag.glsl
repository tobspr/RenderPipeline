#version 400


#pragma include "../SMAAWrap.inc.glsl"

uniform sampler2D EdgeTex;
uniform sampler2D AreaTex;
uniform sampler2D SearchTex;

uniform int JitterIndex;

in vec2 texcoord;
out vec4 result;

void main() {

    // "Vertex shader"
    vec4 offset[3];
    vec2 pixcoord;
    SMAABlendingWeightCalculationVS(texcoord, pixcoord, offset);

    vec4 subsampleIndices = JitterIndex == 0 ? vec4(1, 1, 1, 0) : vec4(2, 2, 2, 0);


    // Actual Fragment shader
    result = SMAABlendingWeightCalculationPS(texcoord, pixcoord, offset, EdgeTex, AreaTex, SearchTex, subsampleIndices);
    
}