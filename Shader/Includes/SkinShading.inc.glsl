#pragma once



vec3 SkinTransmittance(float distance_through_medium) {
    float weight = 20.0;
    float s = distance_through_medium * weight;
    float s_sq = -s * s;
    vec3 t = vec3(0.233, 0.455, 0.649) * exp(s_sq / 0.0064) +
             vec3(0.1,   0.336, 0.344) * exp(s_sq / 0.0484) +
             vec3(0.118, 0.198, 0.0)   * exp(s_sq / 0.187)  +
             vec3(0.113, 0.007, 0.007) * exp(s_sq / 0.567)  +
             vec3(0.358, 0.004, 0.0)   * exp(s_sq / 1.99)   +
             vec3(0.078, 0.0,   0.0)   * exp(s_sq / 7.41);
    // t *= 0.1;
    // return pow(t, vec3(2.2));
    return pow(t, vec3(1.0 / 2.2));
    // return t;
}


