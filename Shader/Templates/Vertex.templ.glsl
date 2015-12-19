#version 430

%DEFINES%

#pragma include "Includes/Configuration.inc.glsl"
#pragma include "Includes/Structures/VertexOutput.struct.glsl"

in vec4 p3d_Vertex;
in vec3 p3d_Normal;
in vec2 p3d_MultiTexCoord0;

uniform mat4 p3d_ViewProjectionMatrix;
uniform mat4 lastViewProjMatNoJitter;
uniform mat4 trans_model_to_world;
uniform mat3 tpose_world_to_model;

out layout(location=0) VertexOutput vOutput;

uniform struct {
    vec4 diffuse;
    vec3 specular;
    vec4 ambient;
} p3d_Material;

%INCLUDES%
%INOUT%

void main() {
    vOutput.texcoord = p3d_MultiTexCoord0;
    vOutput.normal = normalize(tpose_world_to_model * p3d_Normal).xyz;
    vOutput.position = (trans_model_to_world * p3d_Vertex).xyz;

    // @TODO: Use last frame model matrix.
    vOutput.last_proj_position = lastViewProjMatNoJitter * (trans_model_to_world * p3d_Vertex);

    // Get material properties
    vOutput.material_color     = p3d_Material.diffuse.xyz;
    vOutput.material_specular  = p3d_Material.specular.r;
    vOutput.material_metallic  = p3d_Material.specular.g;
    vOutput.material_roughness = p3d_Material.specular.b;
    vOutput.bumpmap_factor     = p3d_Material.diffuse.w;

    %VERTEX%

    gl_Position = p3d_ViewProjectionMatrix * vec4(vOutput.position, 1);
    
    %TRANSFORMATION%
}
