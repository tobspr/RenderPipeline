#version 440

#pragma include "scattering_common.glsl"


layout(local_size_x = 16, local_size_y = 16) in;

uniform writeonly image2D dest;

float opticalDepth(float H, float r, float mu) {
    float result = 0.0;
    float dx = limit(r, mu) / float(TRANSMITTANCE_INTEGRAL_SAMPLES);
    float xi = 0.0;
    float yi = exp(-(r - Rg) / H);
    for (int i = 1; i <= TRANSMITTANCE_INTEGRAL_SAMPLES; ++i) {
        float xj = float(i) * dx;
        float yj = exp(-(sqrt(r * r + xj * xj + 2.0 * xj * r * mu) - Rg) / H);
        result += (yi + yj) / 2.0 * dx;
        xi = xj;
        yi = yj;
    }
    return mu < -sqrt(1.0 - (Rg / r) * (Rg / r)) ? 1e9 : result;
}


void main() {

    ivec2 coord = ivec2(gl_GlobalInvocationID.xy);
    float r, muS;
    getTransmittanceRMu(r, muS);
    vec3 depth = betaR * opticalDepth(HR, r, muS) + betaMEx * opticalDepth(HM, r, muS);
    imageStore(dest, coord, vec4(exp(-depth), SCAT_DEBUG_ALPHA));

}