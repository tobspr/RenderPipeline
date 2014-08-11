#version 400

in vec4 p3d_Vertex;
in vec2 p3d_MultiTexCoord0;
in vec3 p3d_Normal;
uniform mat4 trans_model_to_world;
out vec4 worldPosition;
out vec2 vtxTexcoord;
out vec3 vtxNormal;

void main() {
    vec4 worldPos = trans_model_to_world * p3d_Vertex;
    
    // Depth offset??
    // vec4 worldNormal = trans_model_to_world * vec4(p3d_Normal, 0);
    // worldPos -= worldNormal;

    vtxTexcoord = p3d_MultiTexCoord0;
    gl_Position = worldPos;
    
    vec4 normalWorld = normalize(trans_model_to_world * vec4(p3d_Normal, 0));
    vtxNormal = normalWorld.xyz;
}