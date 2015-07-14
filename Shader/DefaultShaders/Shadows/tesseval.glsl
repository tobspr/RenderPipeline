#version 400

// This shader takes the inputs from tesscontrol and generates the actual
// vertices from that

#pragma include "Includes/Configuration.include"


layout(triangles, equal_spacing, ccw) in;

in vec4 transWorldPos[];

uniform mat4 p3d_ViewProjectionMatrix;

void main()
{
    float u = gl_TessCoord.x;
    float v = gl_TessCoord.y;

    vec4 newWorldPos = transWorldPos[0] * gl_TessCoord.x + transWorldPos[1] * gl_TessCoord.y + transWorldPos[2] * gl_TessCoord.z;
    gl_Position = p3d_ViewProjectionMatrix * newWorldPos;
}