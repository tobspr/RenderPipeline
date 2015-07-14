#version 430

#pragma include "Includes/Structures/VertexOutput.struct"

layout(vertices = 3) out;

in VertexOutput vOutput[];
out VertexOutput tcOutput[];

// This two variables determine the tesselation
float TessLevelInner = 4.0;
float TessLevelOuter = 4.0;

#define ID gl_InvocationID

void main()
{
    tcOutput[ID] = vOutput[ID];

    if (ID == 0) {

        // -- if you need to compute any tesselation factors, do it here --

        gl_TessLevelInner[0] = TessLevelInner;
        gl_TessLevelOuter[0] = TessLevelOuter;
        gl_TessLevelOuter[1] = TessLevelOuter;
        gl_TessLevelOuter[2] = TessLevelOuter;
    }
}