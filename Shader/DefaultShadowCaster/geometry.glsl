#version 410
#pragma optionNV (unroll all)


#include "Includes/Configuration.include"
#include "Includes/ShadowSource.include"
#include "Includes/ParabolicTransform.include"

uniform mat4 p3d_ModelViewProjectionMatrix;

layout(triangles) in;
layout(triangle_strip, max_vertices=SHAODOW_GEOMETRY_MAX_VERTICES) out;

uniform int numUpdates;
uniform ShadowSource updateSources[SHADOW_MAX_UPDATES_PER_FRAME];

in vec2 vtxTexcoord[3];
in vec3 vtxNormal[3];
out vec2 texcoord;
out vec3 normal;

void main() {
  for (int pass = 0; pass < numUpdates; pass ++) {
    ShadowSource currentSource = updateSources[pass];
    mat4 mvp = currentSource.mvp;
    gl_ViewportIndex = pass + 1;
    for(int i=0; i<3; i++)
    {
      gl_Position = mvp * gl_in[i].gl_Position;
      texcoord = vtxTexcoord[i];
      normal = vtxNormal[i];

      // gl_Position = transformParabol(gl_Position, currentSource.nearPlane, currentSource.farPlane);
      // if (gl_Position.w >= 0.0) { 
        EmitVertex();
      // }
    }
    EndPrimitive();    
  }
}
