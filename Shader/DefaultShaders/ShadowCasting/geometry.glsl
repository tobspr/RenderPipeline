#version 410


#pragma include "Includes/Configuration.include"
#pragma include "Includes/ShadowSource.include"
#pragma include "Includes/ParabolicTransform.include"

uniform mat4 p3d_ModelViewProjectionMatrix;

layout(triangles) in;
layout(triangle_strip, max_vertices=SHADOW_GEOMETRY_MAX_VERTICES) out;

uniform int numUpdates;
uniform ShadowSource updateSources[SHADOW_MAX_UPDATES_PER_FRAME];

in vec2 vtxTexcoord[3];
out vec2 texcoord;

void main() {
  for (int pass = 0; pass < numUpdates; pass ++) {
    ShadowSource currentSource = updateSources[pass];
    gl_ViewportIndex = pass + 1;
    for(int i=0; i< gl_in.length(); i++)
    {
      gl_Position = currentSource.mvp * gl_in[i].gl_Position;
      texcoord = vtxTexcoord[i];
      EmitVertex();
    }
    EndPrimitive();    
  }
}
