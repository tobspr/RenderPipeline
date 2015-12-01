#pragma once

#pragma include "Includes/Configuration.inc.glsl"

vec3 sun_vector = sun_azimuth_to_angle(
        TimeOfDay.Scattering.sun_azimuth,
        TimeOfDay.Scattering.sun_altitude);

uniform sampler3D ScatteringLUT;


vec3 get_scattering(vec3 surface_pos) {

    surface_pos = normalize(surface_pos);
    // surface_pos.z = max(0.2, surface_pos.z);
    // if (surface_pos.z < 0) return vec3(0.1, 0, 0);

    float elevation, theta, radius;
    vector_to_spherical(surface_pos, theta, elevation, radius);

    float sun_elevation = TimeOfDay.Scattering.sun_altitude / 180.0 * M_PI;
    float sun_azimuth = TimeOfDay.Scattering.sun_azimuth / 180.0 * M_PI;

    float night_factor = saturate(sun_elevation * 30.0);

    float max_angle_factor = 40.0 / 180.0 * M_PI;
    float elevation_factor = sun_elevation / max_angle_factor;

    float slice_index = 0.5 / 100.0 + elevation_factor; 


    float factor_x = theta;
    float factor_y = elevation;

    float neg_solar_elevation = HALF_PI - sun_elevation;

    float cos_gamma = cos(elevation) * cos(neg_solar_elevation)
        + sin(elevation) * sin(neg_solar_elevation)
        * cos(theta - sun_azimuth + M_PI);

    float gamma = acos(cos_gamma);

    elevation *= 0.95;

    vec2 lut_coord = vec2(gamma / TWO_PI, 1 - (elevation / HALF_PI));
    vec3 value = textureLod(ScatteringLUT, vec3(lut_coord, slice_index), 0).xyz ;


    // value = pow(value, vec3(1.5));
    value = value - 0.005;
    value *= 25.0;

    // value = value / (1 + value);

    value *= night_factor;

    return vec3(value);

}


vec3 get_scattering_at_surface(vec3 surface_pos) {

    vec3 vec_to_cam = vec3(surface_pos - cameraPosition);

    surface_pos.xy = vec2(vec_to_cam.xy * 0.6);
    // surface_pos.xy /= surface_pos.z * 0.01;
    // vec3 v = normalize(surface_pos);
    return get_scattering(surface_pos);
}

vec3 DoScattering(vec3 surface_pos, vec3 view_dir, out float fog_factor)
{
    
    // Move surface pos above ocean level
    if (surface_pos.z < -0.01) {
        vec3 v2s = surface_pos - cameraPosition;
        float z_factor = abs(cameraPosition.z) / abs(v2s.z);
        surface_pos = cameraPosition + v2s * z_factor;
        view_dir = normalize(surface_pos - cameraPosition);
    }


    float path_length = distance(surface_pos, cameraPosition);

    vec3 inscatter = get_scattering(surface_pos);

    fog_factor = 1.0;

    // surface
    if (path_length < 20000.0) {

        // integrate scattering
        const int num_steps = 6;
        float curr_h = cameraPosition.z;

        curr_h *= 1.0 - saturate(path_length / 30000.0);

        float h_step = (surface_pos.z - cameraPosition.z) / num_steps;
        vec3 accum = vec3(0);
        for (int i = 0; i < num_steps; ++i) {
            curr_h += h_step;
            accum += get_scattering_at_surface(vec3(surface_pos.xy, curr_h));
        }

        accum /= float(num_steps);

        float fog_ramp = TimeOfDay.Scattering.fog_ramp_size;
        float fog_start = TimeOfDay.Scattering.fog_start;

        // fog_factor = smoothstep(0, 1, (path_length-fog_start) / fog_ramp);
        fog_factor = smoothstep(0, 1, 1-exp( -(path_length-fog_start) / (0.5*fog_ramp) ) );

        // Exponential height fog
        fog_factor *= exp(- pow( max(0,surface_pos.z), 1.2) / (5.0 * GET_SETTING(Scattering, ground_fog_factor) ));

        // accum *= mix(TimeOfDay.Scattering.fog_brightness * 1.6, 1.0, saturate(path_length / 20000.0));
        accum *= fog_factor;

        inscatter = accum;

        fog_factor = saturate(1.2 * fog_factor);
    }

    // return get_scattering(surfacePos);


    return inscatter;
}

