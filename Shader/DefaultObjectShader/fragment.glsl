#version 150

#include "Includes/VertexOutput.include"

// Input from the vertex shader
in VertexOutput vOutput;

// Textures Samplers
uniform sampler2D p3d_Texture0;
uniform sampler2D p3d_Texture1;
uniform sampler2D p3d_Texture2;
uniform sampler2D p3d_Texture3;
// uniform sampler2D p3d_Texture4;

// This is required for the materials
#include "Includes/MaterialPacking.include"


void main() {



    // Create a material to store the properties on
    Material m;

    vec3 normal = normalize(vOutput.normalWorld);
    // vec3 diffuse = vec3(1.0);

    vec3 bump = texture(p3d_Texture1, vOutput.texcoord).rgb*2.0 - 1.0;

    normal = normalize(normal + bump * 0.05);
    // normal = normalize(normal);

    vec4 diffuse = texture(p3d_Texture0, vOutput.texcoord);
    vec4 rawSpecular = texture(p3d_Texture2, vOutput.texcoord);

    diffuse.rgb = vec3(1.0);

    float specular = 0.0;

    // if (diffuse.a < 0.5) discard;

    // specular = 0;

    // vec3 diffuse = vec3(1);

    m.metallic = 0.0;
    m.roughness = 0.0;
    // m.specular = rawSpecular.x;
    m.specular = 0.0;
    m.baseColor = diffuse.rgb;
    m.position = vOutput.positionWorld;
    m.normal = normal;

    // Pack material and output to the render targets
    renderMaterial(m);
}