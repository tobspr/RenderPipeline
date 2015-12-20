#pragma once

/*
From:
http://www.iryoku.com/translucency/
*/

const float skin_gamma = 1.0 / 2.2;
const float skin_travel_weight = 20.0;
const float skin_transmittance_factor = 0.8;

vec3 skin_transmittance(float distance_through_medium) {
    float s = distance_through_medium * skin_travel_weight;
    float s_sq = -s * s;
    vec3 t = vec3(0.233, 0.455, 0.649) * exp(s_sq / 0.0064) +
             vec3(0.1,   0.336, 0.344) * exp(s_sq / 0.0484) +
             vec3(0.118, 0.198, 0.0)   * exp(s_sq / 0.187)  +
             vec3(0.113, 0.007, 0.007) * exp(s_sq / 0.567)  +
             vec3(0.358, 0.004, 0.0)   * exp(s_sq / 1.99)   +
             vec3(0.078, 0.0,   0.0)   * exp(s_sq / 7.41);
    return pow(t * skin_transmittance_factor, vec3(skin_gamma));
}


