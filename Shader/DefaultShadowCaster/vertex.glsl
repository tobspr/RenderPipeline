#version 400

in vec4 p3d_Vertex;
// in vec3 p3d_Normal;
uniform mat4 trans_model_to_world;
out vec4 worldPosition;

void main() {
    vec4 worldPos = trans_model_to_world * p3d_Vertex;
    
    // Depth offset??
    // vec4 worldNormal = trans_model_to_world * vec4(p3d_Normal, 0);
    // worldPos -= worldNormal;

    gl_Position = worldPos;

}