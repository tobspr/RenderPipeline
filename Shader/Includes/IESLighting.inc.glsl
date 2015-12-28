#pragma once

#pragma include "Includes/Configuration.inc.glsl"

uniform sampler3D IESDatasetTex;

// Scale all ies values, since they look way too dark otherwise.
const float IES_SCALE = 1.0;

// Computes the IES factor from a given light vector and profile.
// A profile < 0 means no light profile.
float get_ies_factor(vec3 light_vector, int profile) {
    if (profile < 0) return 1.0;
    light_vector = normalize(light_vector);
    float horiz_angle = acos(light_vector.z) / M_PI;
    float vert_angle = fma(atan(light_vector.x, light_vector.y), 1.0 / TWO_PI, 0.5);
    float profile_coord = (profile+0.5) / MAX_IES_PROFILES;
    float data = textureLod(IESDatasetTex, vec3(horiz_angle, vert_angle, profile_coord), 0).x;
    return data * IES_SCALE;
}

// Computes the IES factor from a given spherical coordinate and profile.
// theta and phi should range from 0 to 1.
float get_ies_factor(int profile, float theta, float phi) {
    if (profile < 0) return 1.0;
    float profile_coord = (profile+0.5) / MAX_IES_PROFILES;
    float data = textureLod(IESDatasetTex, vec3(theta * 0.5 + 0.5, phi, profile_coord), 0).x;
    return data * IES_SCALE;
}
