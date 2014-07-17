#version 400

#include "Includes/Configuration.include"
#include "Includes/VertexOutput.include"


// This shader creates the triangles 
layout(triangles, equal_spacing, ccw) in;

in VertexOutput tcOutput[];
out VertexOutput vOutput;


uniform mat4 p3d_ModelViewProjectionMatrix;

uniform sampler2D p3d_Texture4;


#define INTERPOLATE(prop) mix( mix(tcOutput[0]. prop , tcOutput[1]. prop , u),  mix(tcOutput[3]. prop , tcOutput[2]. prop , u), v)


#define INTERPOLATE3(prop) \
( tcOutput[0] . prop ) * gl_TessCoord.x + \
( tcOutput[1] . prop ) * gl_TessCoord.y + \
( tcOutput[2] . prop ) * gl_TessCoord.z


uniform mat4 lastMVP;

void main()
{
    float u = gl_TessCoord.x;
    float v = gl_TessCoord.y;

    vOutput = tcOutput[0];
    vOutput.positionWorld = INTERPOLATE3(positionWorld);
    vOutput.normalWorld = INTERPOLATE3(normalWorld);
    vOutput.texcoord = INTERPOLATE3(texcoord);

    vOutput.materialDiffuse = INTERPOLATE3(materialDiffuse);
    vOutput.materialSpecular = INTERPOLATE3(materialSpecular);
    vOutput.materialAmbient = INTERPOLATE3(materialAmbient);
    vOutput.lastProjectedPos = INTERPOLATE3(lastProjectedPos);

    float displace = texture(p3d_Texture4, vOutput.texcoord);
    // displace = 0.0;
    // vOutput.positionWorld.z += 0.12 * displace;

    vOutput.lastProjectedPos = FAST_mul(lastMVP, vOutput.positionWorld) * vec4(1,1,1,2);



    gl_Position = p3d_ModelViewProjectionMatrix * vec4(vOutput.positionWorld, 1);
}