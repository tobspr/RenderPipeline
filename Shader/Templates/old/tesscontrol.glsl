#version 430

#pragma include "Includes/Structures/VertexOutput.struct"

layout(vertices = 3) out;

in VertexOutput vOutput[];
out VertexOutput tcOutput[];


#define ID gl_InvocationID

#pragma ENTRY_POINT SHADER_IN_OUT

void main()
{
    tcOutput[ID] = vOutput[ID];




    if (ID == 0) {
        // This two variables determine the tesselation
        float TessLevelInner = 4.0;
        float TessLevelOuter = 4.0;

        #pragma ENTRY_POINT TESS_LEVEL

        gl_TessLevelInner[0] = TessLevelInner;
        gl_TessLevelOuter[0] = TessLevelOuter;
        gl_TessLevelOuter[1] = TessLevelOuter;
        gl_TessLevelOuter[2] = TessLevelOuter;
    }
}