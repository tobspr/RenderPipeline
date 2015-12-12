#version 430

%DEFINES%

#define IS_SHADOW_SHADER 1

#pragma include "Includes/Configuration.inc.glsl"
#pragma include "Includes/Structures/VertexOutput.struct.glsl"

%INCLUDES%

%INOUT%

out vec4 result;

layout(location=0) in VertexOutput vOutput;

uniform sampler2D p3d_Texture0;

void main() {

    float sampled_alpha = texture(p3d_Texture0, vOutput.texcoord).w;

    if (sampled_alpha < 0.8) discard;


    result = vec4(1.0, 0.6, 0.2, 1.0);
}
