#pragma once

// Structure used in the Material Templates
struct MaterialShaderOutput {
    vec3 basecolor;
    vec3 normal;
    float roughness;
    float specular;
    float metallic;
    float translucency;
};



// Structure actually stored in the GBuffer, this *may* differ but not necessarily has to:
struct Material {
    vec3 basecolor;
    vec3 normal;
    vec3 position;
    float roughness;
    float specular;
    float metallic;
    float translucency;
    float diffuse_aa;
};

