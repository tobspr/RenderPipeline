#pragma once

struct VertexOutput {
    vec2 texcoord;
    vec3 normal;
    vec3 position;
    vec4 last_proj_position;
    
    // material properties
    vec3 material_color;
    float material_specular;
    float material_metallic;
    float material_roughness;
    float bumpmap_factor;
};
