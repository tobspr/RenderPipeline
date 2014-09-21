#version 400

// This shader takes the inputs from tesscontrol and generates the actual
// vertices from that

#include "Includes/Configuration.include"
#include "Includes/VertexOutput.include"

layout(triangles, equal_spacing, ccw) in;

in VertexOutput tcOutput[];
out VertexOutput vOutput;
uniform mat4 p3d_ModelViewProjectionMatrix;
uniform sampler2D p3d_Texture4;

// Quad interpolation
#define INTERPOLATE(prop) mix( mix(tcOutput[0]. prop , tcOutput[1]. prop , u),  mix(tcOutput[3]. prop , tcOutput[2]. prop , u), v)

// Triangle interpolation
#define INTERPOLATE3(prop) \
( tcOutput[0] . prop ) * gl_TessCoord.x + \
( tcOutput[1] . prop ) * gl_TessCoord.y + \
( tcOutput[2] . prop ) * gl_TessCoord.z

uniform mat4 p3d_ViewProjectionMatrix;

void main()
{
    float u = gl_TessCoord.x;
    float v = gl_TessCoord.y;

    vOutput.positionWorld = INTERPOLATE3(positionWorld);
    vOutput.normalWorld = INTERPOLATE3(normalWorld);
    vOutput.texcoord = INTERPOLATE3(texcoord);
    vOutput.materialDiffuse = INTERPOLATE3(materialDiffuse);
    vOutput.materialSpecular = INTERPOLATE3(materialSpecular);
    vOutput.materialAmbient = INTERPOLATE3(materialAmbient);
    vOutput.lastProjectedPos = INTERPOLATE3(lastProjectedPos);

    // float displace = texture(p3d_Texture4, vOutput.texcoord);
    // vOutput.positionWorld.z += 0.12 * displace;

    // It is important to only use the view projection matrix here, because the position
    // is already in world space, so no need for the model matrix
    gl_Position = p3d_ViewProjectionMatrix * vec4(vOutput.positionWorld, 1.0);
}