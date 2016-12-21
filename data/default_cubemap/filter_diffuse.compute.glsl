#version 430

// Shader to pre-filter the cubemap using importance sampling

layout (local_size_x = 16, local_size_y = 16, local_size_z = 1) in;


#define M_PI 3.1415926535897932384626433

float rand(vec2 co){
  return abs(fract(sin(dot(co.xy ,vec2(12.9898,78.233))) * 43758.5453)) * 2 - 1;
}

vec3 get_transformed_coord(vec2 coord, uint face) {
    float f = 1.0;
    switch (face) {
        case 1: return vec3(-f, coord);
        case 2: return vec3(coord, -f);
        case 0: return vec3(f, -coord.x, coord.y);
        case 3: return vec3(coord.xy * vec2(1, -1), f);
        case 4: return vec3(coord.x, f, coord.y);
        case 5: return vec3(-coord.x, -f, coord.y);
    }
    return vec3(0);
}

// From:
// http://www.trentreed.net/blog/physically-based-shading-and-image-based-lighting/
vec2 hammersley(uint i, uint N)
{
    return vec2(float(i) / float(N), float(bitfieldReverse(i)) * 2.3283064365386963e-10);
}

// Converts a normalized spherical coordinate (r = 1) to cartesian coordinates
vec3 spherical_to_cartesian(float theta, float phi) {
    float sin_theta = sin(theta);
    return normalize(vec3(
        sin_theta * cos(phi),
        sin_theta * sin(phi),
        cos(theta)
    ));
}

vec3 importance_sample_lambert(vec2 Xi)
{
    float phi = 2.0 * M_PI * Xi.x;
    float cos_theta_sq = Xi.y;
    float cos_theta = sqrt(cos_theta_sq);
    float sin_theta = sqrt(1 - Xi.y);
    return vec3(sin_theta * cos(phi), sin_theta * sin(phi), cos_theta);
}


// Finds a tangent and bitangent vector based on a given normal
void find_arbitrary_tangent(vec3 normal, out vec3 tangent, out vec3 bitangent) {
    vec3 v0 = abs(normal.z) < 0.999 ? vec3(0, 0, 1) : vec3(0, 1, 0);
    tangent = normalize(cross(v0, normal));
    bitangent = normalize(cross(tangent, normal));
}

vec3 transform_cubemap_coordinates(vec3 coord) {
    return normalize(coord.xyz * vec3(1, -1, 1));
}

// Converts a normalized vector to spherical coordinates
void cartesian_to_spherical(vec3 v, out float theta, out float phi) {
    phi = acos(v.z);
    theta = atan(v.y, v.x) + M_PI;
}


uniform sampler2D SourceTex;
uniform int currentFace;
uniform int totalSize;
layout(rgba16f) uniform imageCube DestTex;

void main() {
    ivec2 coord = ivec2(gl_GlobalInvocationID.xy);

    vec2 texcoord = vec2(coord + 0.5) / float(totalSize);
    texcoord = texcoord * 2.0 - 1.0;

    vec3 n = normalize(get_transformed_coord(texcoord, currentFace));

    vec3 tangent, binormal;
    find_arbitrary_tangent(n, tangent, binormal);

    vec4 accum = vec4(0);
    uint num_samples = 100000;

    vec2 local_seed = coord * 0.34238759;
    float offset = rand(local_seed);

    for (uint i = 0; i < num_samples; ++i) {
        vec2 xi = hammersley(i, num_samples);
        xi.x = mod(xi.x + offset / num_samples * 2.62192854, 1.0);
        xi.y = mod(xi.y + offset * 3.2847293841, 1.0);

        vec3 r = importance_sample_lambert(xi);
        vec3 h = normalize(r.x * tangent + r.y * binormal + r.z * n);
        vec3 l = 2.0 * dot(n, h) * h - n;

        float NxL = clamp(dot(n, l), 0.0, 1.0);
        float phi, theta;
        cartesian_to_spherical(l, theta, phi);

        vec3 sampled = textureLod(SourceTex, vec2(theta / (2.0 * M_PI), phi / M_PI), 0).rgb * NxL;
        accum += vec4(sampled, NxL);
    }

    accum /= max(0.1, accum.w);
    accum *= 15.0;
    // accum *= 5.0;
    // accum /= M_PI;

    imageStore(DestTex, ivec3(coord, currentFace), vec4(accum.xyz, 1.0));
}
