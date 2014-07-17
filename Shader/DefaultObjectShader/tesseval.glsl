#version 400

#include "Includes/VertexOutput.include"


// This shader creates the triangles 
layout(quads, equal_spacing, ccw) in;

in VertexOutput tcOutput[];
out VertexOutput vOutput;


uniform mat4 p3d_ModelViewProjectionMatrix;

uniform sampler2D p3d_Texture3;


#define INTERPOLATE(prop) mix( mix(tcOutput[0]. prop , tcOutput[1]. prop , u),  mix(tcOutput[3]. prop , tcOutput[2]. prop , u), v)


void main()
{
    float u = gl_TessCoord.x;
    float v = gl_TessCoord.y;

    vOutput = tcOutput[0];
    vOutput.positionWorld = INTERPOLATE(positionWorld);
    vOutput.normalWorld = INTERPOLATE(normalWorld);
    vOutput.materialDiffuse = INTERPOLATE(materialDiffuse);
    vOutput.texcoord = INTERPOLATE(texcoord);

    float displace = texture(p3d_Texture3, vOutput.texcoord);
    vOutput.positionWorld.z += 0.1 * displace;


    gl_Position = p3d_ModelViewProjectionMatrix * vec4(vOutput.positionWorld, 1);
}