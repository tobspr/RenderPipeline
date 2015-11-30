#pragma once

#pragma include "Includes/Configuration.inc.glsl"

vec3 sun_vector = sun_azimuth_to_angle(
        TimeOfDay.Scattering.sun_azimuth,
        TimeOfDay.Scattering.sun_altitude);


vec3 DoScattering(vec3 surfacePos, vec3 viewDir, out float fog_factor)
{
    return vec3(max(0, viewDir.z));
}