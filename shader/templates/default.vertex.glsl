#version 430

%DEFINES%

#define USE_MAIN_SCENE_DATA
#pragma include "Includes/Configuration.inc.glsl"
#pragma include "Includes/Structures/VertexOutput.struct.glsl"
#pragma include "Includes/Structures/MaterialOutput.struct.glsl"


in vec4 p3d_Vertex;
in vec3 p3d_Normal;
in vec2 p3d_MultiTexCoord0;

uniform mat4 p3d_ViewProjectionMatrix;
uniform mat4 trans_model_to_world;
uniform mat3 tpose_world_to_model;

out layout(location=0) VertexOutput vOutput;
out layout(location=4) flat MaterialOutput mOutput;

uniform struct {
    vec4 baseColor;
    vec4 emission;
    float roughness;
    float metallic;
    float refractiveIndex;
} p3d_Material;

%INCLUDES%
%INOUT%

void main() {
    vOutput.texcoord = p3d_MultiTexCoord0;
    vOutput.normal = normalize(tpose_world_to_model * p3d_Normal).xyz;
    vOutput.position = (trans_model_to_world * p3d_Vertex).xyz;

    // @TODO: Use last frame model matrix. Need to somehow set it as a shader
    // input, to be able to use it here. We also somehow have to account for
    // skinning, we can maybe use hardware skinning for this.
    vOutput.last_proj_position = MainSceneData.last_view_proj_mat_no_jitter * (trans_model_to_world * p3d_Vertex);

    // Get material properties
    mOutput.color          = p3d_Material.baseColor.xyz;
    mOutput.specular_ior   = p3d_Material.refractiveIndex;
    mOutput.metallic       = p3d_Material.metallic;
    mOutput.roughness      = p3d_Material.roughness;
    mOutput.normalfactor   = p3d_Material.emission.r;
    mOutput.translucency   = p3d_Material.emission.b;
    mOutput.transparency   = p3d_Material.baseColor.w;
    mOutput.emissive       = p3d_Material.emission.w;

    %VERTEX%

    gl_Position = p3d_ViewProjectionMatrix * vec4(vOutput.position, 1);
    
    %TRANSFORMATION%
}
