#version 400

// This shader takes the inputs from tesscontrol and generates the actual
// vertices from that

#pragma include "Includes/Configuration.include"


layout(triangles, equal_spacing, ccw) in;

in vec4 transWorldPos[];
in vec2 transTexcoord[];

out vec2 texcoord;

uniform mat4 p3d_ViewProjectionMatrix;

#pragma ENTRY_POINT SHADER_IN_OUT

void main()
{
    float u = gl_TessCoord.x;
    float v = gl_TessCoord.y;

    vec4 newWorldPos = transWorldPos[0] * gl_TessCoord.x + transWorldPos[1] * gl_TessCoord.y + transWorldPos[2] * gl_TessCoord.z;
    texcoord = transTexcoord[0] * gl_TessCoord.x + transTexcoord[1] * gl_TessCoord.y + transTexcoord[2] * gl_TessCoord.z;

    #pragma ENTRY_POINT PARAMETER_LERP

    gl_Position = p3d_ViewProjectionMatrix * newWorldPos;
}