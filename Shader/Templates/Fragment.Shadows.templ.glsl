#version 430

%DEFINES%

#define IS_SHADOW_SHADER 1

#pragma include "Includes/Configuration.inc.glsl"

%INCLUDES%

%INOUT%

out vec4 result;

void main() {
    result = vec4(1.0, 0.6, 0.2, 1.0);
}
