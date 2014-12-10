#version 400

in vec4 p3d_Vertex;
in vec4 p3d_Normal;
in vec2 p3d_MultiTexCoord0;
uniform mat4 trans_model_to_world;
out vec4 worldPos;
out vec2 vtxTexcoord;
out vec3 vtxDiffuseMultiplier;

uniform struct PandaMaterial {
    vec4 diffuse;
    vec3 specular;
    vec4 ambient;
} p3d_Material;

void main() {
    worldPos = trans_model_to_world * p3d_Vertex;
    
    // Depth offset??
    vec4 worldNormal = trans_model_to_world * vec4(p3d_Normal.xyz, 0);
    // worldPos -= worldNormal;

    // Todo: Diffuse Multiplier = Material diffuse * Material GI Factor
    // vtxDiffuseMultiplier = vec3(1);
    vtxDiffuseMultiplier = p3d_Material.diffuse.rgb * clamp(1.0 - p3d_Material.diffuse.b*0.8, 0.0, 1.0);
    // vtxDiffuseMultiplier = p3d_Material.diffuse.rgb;
// 
    vtxTexcoord = p3d_MultiTexCoord0;
    gl_Position = worldPos;   
}