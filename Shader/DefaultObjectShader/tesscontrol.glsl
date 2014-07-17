#version 440

#include "Includes/VertexOutput.include"

// Compute the tesselation factors here
layout(vertices = 4) out;

in VertexOutput vOutput[];
out VertexOutput tcOutput[];

float TessLevelInner = 60.0;
float TessLevelOuter = 60.0;

#define ID gl_InvocationID

void main()
{
    tcOutput[ID] = vOutput[ID];
    if (ID == 0) {
        gl_TessLevelInner[0] = TessLevelInner;
        gl_TessLevelInner[1] = TessLevelInner;
        gl_TessLevelOuter[0] = TessLevelOuter;
        gl_TessLevelOuter[1] = TessLevelOuter;
        gl_TessLevelOuter[2] = TessLevelOuter;
        gl_TessLevelOuter[3] = TessLevelOuter;
    }
}