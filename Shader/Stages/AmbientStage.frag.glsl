#version 400

#pragma include "Includes/Configuration.inc.glsl"
#pragma include "Includes/GBufferPacking.inc.glsl"
#pragma include "Includes/BRDF.inc.glsl"

in vec2 texcoord;
uniform sampler2D ShadedScene;
uniform sampler2D GBufferDepth;
uniform sampler2D GBuffer0;
uniform sampler2D GBuffer1;
uniform sampler2D GBuffer2;

uniform samplerCube DefaultEnvmap;
uniform vec3 cameraPosition;

out vec4 result;

float get_mipmap_for_roughness(samplerCube map, float roughness) {
    int cubemap_size = textureSize(map, 0).x;
    float num_mipmaps = 1 + floor(log2(cubemap_size));
    float reflectivity = 1.0 - roughness;
    return num_mipmaps - 2 - reflectivity * 7.0;
}


vec3 fresnel_with_roughness(vec3 specular_color, float VxH, float roughness, float metallic) {
    return mix(BRDFSchlick(specular_color, VxH, roughness), specular_color, max(roughness, metallic) ) * (2.0 - roughness);

}

void main() {

    Material m = unpack_material(GBufferDepth, GBuffer0, GBuffer1, GBuffer2);
    vec3 view_vector = normalize(m.position - cameraPosition);
    vec4 ambient = vec4(0);

    vec3 reflection_coord = reflect(view_vector, m.normal);
    vec3 env_coord = fix_cubemap_coord(reflection_coord);
    float env_mipmap = get_mipmap_for_roughness(DefaultEnvmap, m.roughness);
    vec3 env_default_color = textureLod(DefaultEnvmap, env_coord, env_mipmap).xyz;
    vec3 halfway_vector = normalize(reflection_coord + view_vector);

    vec3 specular_color = m.diffuse * m.specular;
    float VxH = max(0, dot(view_vector, halfway_vector));

    vec3 diffuse_ambient = vec3(0.02) * m.diffuse * (1.0 - m.metallic);
    vec3 specular_ambient = 
        fresnel_with_roughness(specular_color, VxH, m.roughness, m.metallic) *
        env_default_color / M_PI * 0.1;

    ambient.xyz = diffuse_ambient + specular_ambient;
    result = texture(ShadedScene, texcoord) * 1 + ambient * 1;
}