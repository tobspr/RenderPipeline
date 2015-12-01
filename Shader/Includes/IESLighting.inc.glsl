#pragma once

#pragma include "Includes/Configuration.inc.glsl"

uniform sampler3D IESDatasetTex;


float get_ies_factor(vec3 light_vector, int profile) {
    if (profile < 0) return 1.0;

    light_vector = normalize(light_vector);

    float horiz_angle = acos(light_vector.z) / M_PI;
    horiz_angle = 1 -  light_vector.z;
    float vert_angle = fma(atan(light_vector.x, light_vector.y), 1.0 / TWO_PI, 0.5);
    vert_angle = 0;


    float profile_coord = (profile+0.5) / MAX_IES_PROFILES;
    float data = textureLod(IESDatasetTex, vec3(horiz_angle, vert_angle, profile_coord), 0).x;

    // return vert_angle;

    return data * 10.0;
}


// Theta from 0 .. 1, phi from 0 .. 1
float get_ies_factor(int profile, float theta, float phi) {
    if (profile < 0) return 1.0;
    float profile_coord = (profile+0.5) / MAX_IES_PROFILES;
    float data = textureLod(IESDatasetTex, vec3(theta, phi, profile_coord), 0).x;
    return data * 10.0;   
}
