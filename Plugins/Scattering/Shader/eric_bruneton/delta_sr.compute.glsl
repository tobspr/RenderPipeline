#version 440

#pragma include "scattering_common.glsl"

layout(local_size_x = 8, local_size_y = 8, local_size_z = 8) in;

uniform sampler3D deltaJSampler;
uniform writeonly image3D RESTRICT dest;

vec3 integrand(float r, float mu, float muS, float nu, float t) {
    float ri = sqrt(r * r + t * t + 2.0 * r * mu * t);
    float mui = (r * mu + t) / ri;
    float muSi = (nu * t + muS * r) / ri;
    return texture4D(deltaJSampler, ri, mui, muSi, nu).rgb * transmittance(r, mu, t);
}

vec3 inscatter(float r, float mu, float muS, float nu) {
    vec3 raymie = vec3(0.0);
    float dx = limit(r, mu) / float(INSCATTER_INTEGRAL_SAMPLES);
    float xi = 0.0;
    vec3 raymiei = integrand(r, mu, muS, nu, 0.0);
    for (int i = 1; i <= INSCATTER_INTEGRAL_SAMPLES; ++i) {
        float xj = float(i) * dx;
        vec3 raymiej = integrand(r, mu, muS, nu, xj);
        raymie += (raymiei + raymiej) / 2.0 * dx;
        xi = xj;
        raymiei = raymiej;
    }
    return raymie;
}

void main() {
    ivec2 coord = ivec2(gl_GlobalInvocationID.xy);
    int layer = int(gl_GlobalInvocationID.z);

    float r;
    vec4 dhdH;
    get_r_dhdh(layer, r, dhdH);

    float mu, muS, nu;
    getMuMuSNu(r, dhdH, mu, muS, nu);
    vec3 result = inscatter(r, mu, muS, nu);
    imageStore(dest, ivec3(coord, layer), vec4(result, SCAT_DEBUG_ALPHA));
}
