#version 400

#pragma include "Includes/Configuration.inc.glsl"
#pragma include "../SMAAWrap.inc.glsl"

uniform sampler2D BlendTex;
uniform sampler2D ShadedScene;

out vec4 result;

void main() {
    vec2 texcoord = get_texcoord();

    // "Vertex shader"
    vec4 offset;
    SMAANeighborhoodBlendingVS(texcoord, offset);

    // Actual Fragment shader
    #if SMAA_REPROJECTION
        result = SMAANeighborhoodBlendingPS(texcoord, offset, ShadedScene, BlendTex, velocityTex);
    #else
        result = SMAANeighborhoodBlendingPS(texcoord, offset, ShadedScene, BlendTex);
    #endif
}
