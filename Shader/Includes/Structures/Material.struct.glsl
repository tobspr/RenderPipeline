#pragma once

// Structure used in the Material Templates
struct MaterialShaderOutput {
    vec3 basecolor;
    vec3 normal;
    vec3 position;
    float roughness;
    float specular;
    float metallic;
};



// Structure actually stored in the GBuffer
struct Material {
    vec3 normal;
    vec3 diffuse;
    vec3 specular;
    float roughness;
    vec3 position;
};

