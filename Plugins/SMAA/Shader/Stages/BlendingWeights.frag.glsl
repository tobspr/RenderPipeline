#version 400


#pragma include "../SMAAWrap.inc.glsl"

uniform sampler2D EdgeTex;
uniform sampler2D AreaTex;
uniform sampler2D SearchTex;

// uniform sampler2D ShadedScene;

in vec2 texcoord;
out vec4 result;

void main() {

    // "Vertex shader"
    vec4 offset[3];
    vec2 pixcoord;
    SMAABlendingWeightCalculationVS(texcoord, pixcoord, offset);

    vec4 subsampleIndices = vec4(0);

    // Actual Fragment shader
    result = SMAABlendingWeightCalculationPS(texcoord, pixcoord, offset, EdgeTex, AreaTex, SearchTex, subsampleIndices);
    
}