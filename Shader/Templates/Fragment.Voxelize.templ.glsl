#version 430

// Shader used for Voxelization, required for GI

%DEFINES%

#define IS_VOXELIZE_SHADER 1

#pragma include "Includes/Configuration.inc.glsl"
#pragma include "Includes/Structures/VertexOutput.struct.glsl"
#pragma include "Includes/Structures/MaterialOutput.struct.glsl"

%INCLUDES%
%INOUT%

layout(location=0) in VertexOutput vOutput;
layout(location=4) flat in MaterialOutput mOutput;

layout(location=0) out vec4 color0;

// Voxel data
uniform vec3 voxelGridPosition;
uniform int voxelGridRes;
uniform float voxelGridSize;
uniform writeonly image3D RESTRICT VoxelGridDest;

uniform sampler2D p3d_Texture0;

void main() {
    vec3 diffuse = texture(p3d_Texture0, vOutput.texcoord).xyz;
    diffuse *= mOutput.color;
    vec3 shading_result = diffuse;

    // Get destination voxel
    vec3 vs_coord = (vOutput.position - voxelGridPosition + voxelGridSize) / (2.0 * voxelGridSize);
    ivec3 vs_icoord = ivec3(vs_coord * voxelGridRes);

    // Write voxel
    imageStore(VoxelGridDest, vs_icoord, vec4(shading_result, 1));
    color0 = vec4(vs_coord, 1.0);
}

