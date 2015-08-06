#version 410 compatibility

#pragma include "Includes/Configuration.include"
#pragma include "Includes/Structures/VertexOutput.struct"

struct VertexTerrainOutput {
    vec3 positionWorld;
    vec3 normalWorld;
    vec2 texcoord;
    vec4 lastProjectedPos;
    //float fogFactor;
    vec2 texUVrepeat;
    };

uniform sampler2D height;
//uniform vec4 fog;

// Matrices
uniform mat4 trans_model_to_world;
uniform mat4 p3d_ModelViewProjectionMatrix;
uniform mat4 p3d_ModelViewMatrix;
// We need this for the velocity
uniform mat4 lastMVP;
uniform mat4 currentMVP;

in vec4 p3d_Vertex;
in vec3 p3d_Normal;
in vec2 p3d_MultiTexCoord0;

// Outputs
layout(location=0) out VertexTerrainOutput vOutput;

void main()
    {
    float h = texture2DLod(height, p3d_MultiTexCoord0.xy, 0.0).r;   
    //gl_Position = p3d_ModelViewProjectionMatrix * vert;
    vec4 vert=p3d_Vertex;
    vert.z = h*100.0;
    vOutput.positionWorld = (trans_model_to_world * vert).xyz;
    //bloatedNormal = vec4(p3d_Normal, 1.);
    vOutput.normalWorld   = normalize(trans_model_to_world * vec4(p3d_Normal, 0) ).xyz;
    
    // Pass texcoord to fragment shader
    vOutput.texcoord = p3d_MultiTexCoord0;
    //gl_TexCoord[0] = p3d_MultiTexCoord0;
   
    // Compute velocity in vertex shader, but it's important
    // to move the w-divide to the fragment shader
    vOutput.lastProjectedPos = lastMVP * vec4(vOutput.positionWorld, 1) * vec4(1,1,1,2);
   
    vec4 cs_position = p3d_ModelViewMatrix * p3d_Vertex;    
    //float distToEdge = clamp(pow(distance(p3d_Vertex.xyz, vec3(256, 256, 0))/256.0, 4.0), 0.0, 1.0);
    //float distToCamera = clamp(-cs_position.z*fog.a-0.5, 0.0, 1.0);
    //vOutput.fogFactor=clamp(distToCamera+distToEdge, 0.0, 1.0);    
    //texUV=gl_TexCoord[0].xy;
    //texUVrepeat=gl_TexCoord[0].xy*40.0;
    vOutput.texUVrepeat = p3d_MultiTexCoord0.xy * 40.0;
    
    // Transform vertex to window space
    // Only required when not using tesselation shaders
    gl_Position = p3d_ModelViewProjectionMatrix * vert;   
    
    }