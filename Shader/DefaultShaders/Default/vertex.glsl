#version 420

#pragma include "Includes/Configuration.include"
#pragma include "Includes/Structures/VertexOutput.struct"
#pragma include "Includes/Structures/PandaMaterial.struct"

// Matrices
uniform mat4 trans_model_to_world;
uniform mat4 tpose_world_to_model;

// Material properties
in vec4 p3d_Vertex;
in vec3 p3d_Normal;
in vec4 p3d_Color;

// Texture-Coordinate
in vec2 p3d_MultiTexCoord0;

// Outputs
layout(location=0) out VertexOutput vOutput;

uniform PandaMaterial p3d_Material;
uniform vec4 p3d_ColorScale;
uniform mat4 p3d_ModelViewProjectionMatrix;

// We need this for the velocity
uniform mat4 lastMVP;
uniform mat4 currentMVP;


#if defined(IS_DYNAMIC)
    // Vertex index
    in int dovindex;

    uniform int dynamicVtxSplit;

    // Vertex buffers
    uniform coherent layout(rgba32f) image2D dynamicObjectVtxBuffer0;
    uniform coherent layout(rgba32f) image2D dynamicObjectVtxBuffer1;
#endif

#pragma ENTRY_POINT SHADER_IN_OUT

uniform int frameIndex;

void main() {

    // Transform normal to world space
    vOutput.normalWorld = normalize(tpose_world_to_model * vec4(p3d_Normal, 0) ).xyz;

    // Transform position to world space
    vOutput.positionWorld = (trans_model_to_world * p3d_Vertex).xyz;

    // Pass texcoord to fragment shader
    vOutput.texcoord = p3d_MultiTexCoord0.xy;

    // Also pass diffuse to fragment shader
    vOutput.materialDiffuse = p3d_Material.diffuse * p3d_ColorScale * p3d_Color;
    vOutput.materialSpecular = p3d_Material.specular;
    vOutput.materialAmbient = p3d_Material.ambient.z;

    vec4 lastPosWorld = vec4(vOutput.positionWorld, 1);

    // Read last frame vertex position and store current position
    #if defined(IS_DYNAMIC)
        ivec2 vtxIdxPos = ivec2(dovindex % dynamicVtxSplit, dovindex / dynamicVtxSplit);
        int bufferIdx = frameIndex % 2;

        // Ping-Pong rendering to avoid artifacts when reading and writing the same texture
        if (bufferIdx == 0) {
            lastPosWorld = imageLoad(dynamicObjectVtxBuffer0, vtxIdxPos);
            imageStore(dynamicObjectVtxBuffer1, vtxIdxPos, vec4(vOutput.positionWorld, 1));
        } else {
            lastPosWorld = imageLoad(dynamicObjectVtxBuffer1, vtxIdxPos);
            imageStore(dynamicObjectVtxBuffer0, vtxIdxPos, vec4(vOutput.positionWorld, 1));
        }
    #endif

    vOutput.lastProjectedPos = lastMVP * lastPosWorld * vec4(1,1,1,2);

    #pragma ENTRY_POINT SHADER_END

    // Transform vertex to window space
    // Only required when not using tesselation shaders
    gl_Position = currentMVP * vec4(vOutput.positionWorld, 1);
    // gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;

}

