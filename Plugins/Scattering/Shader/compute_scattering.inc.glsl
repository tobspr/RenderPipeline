

// Include local scattering code
#define NO_COMPUTE_SHADER 1
#pragma include "scattering_common.glsl"

uniform sampler3D inscatterSampler;

float sunIntensity = TimeOfDay.Scattering.sun_intensity;
vec3 sunVector = sun_azimuth_to_angle(
        TimeOfDay.Scattering.sun_azimuth,
        TimeOfDay.Scattering.sun_altitude);


vec3 DoScattering(vec3 surfacePos, vec3 viewDir, out float fog_factor)
{

    // Move surface pos above ocean level
    if (surfacePos.z < -0.01) {
        vec3 v2s = surfacePos - cameraPosition;
        float z_factor = abs(cameraPosition.z) / abs(v2s.z);
        surfacePos = cameraPosition + v2s * z_factor;
        viewDir = normalize(surfacePos - cameraPosition);
    }

    vec3 inscatteredLight = vec3(0.0);
    float groundH = Rg + 3.0;
    float pathLength = distance(cameraPosition, surfacePos);
    vec3 startPos = cameraPosition; 

    float height_scale_factor = 0.01;

    float startPosHeight = cameraPosition.z * height_scale_factor + groundH;
    float surfacePosHeight = surfacePos.z * height_scale_factor + groundH;

    float muStartPos = viewDir.z;
    float nuStartPos = max(0, dot(viewDir, sunVector));
    float musStartPos = sunVector.z;

    vec4 inscatter = max(texture4D(inscatterSampler, startPosHeight,
        muStartPos, musStartPos, nuStartPos), 0.0);
        
    fog_factor = 1.0;
    float sun_factor = 1.0; 

    if(pathLength < 20000)
    {

        // Exponential height fog
        float fog_ramp = TimeOfDay.Scattering.fog_ramp_size;
        float fog_start = TimeOfDay.Scattering.fog_start;

        // Exponential, I do not like the look
        // fog_factor = max(0, (1.0 - exp( -pathLength * viewDir.z / fog_end )) / viewDir.z);

        // Looks better IMO
        fog_factor = smoothstep(0, 1, (pathLength-fog_start) / fog_ramp);

        // Produces a smoother transition, but the borders look weird then    
        // fog_factor = pow(fog_factor, 1.0 / 2.2);


        // Get atmospheric color, 3 samples should be enough
        const int num_samples = 3;

        float current_height = max(surfacePos.z, cameraPosition.z);
        float dest_height = surfacePos.z;
        float height_step = (dest_height - current_height) / num_samples;

        vec4 inscatter_sum = vec4(0);
        
        for (int i = 0; i < num_samples; ++i) {
            inscatter_sum += texture4D(inscatterSampler, 
                current_height * height_scale_factor + groundH, 
                mix(current_height / 2000.0 + 0.2, muStartPos, saturate(pathLength / 5000.0) * 0 )
                , musStartPos, nuStartPos);

            current_height += height_step;
        }

        inscatter_sum /= float(num_samples);
        inscatter_sum *= 2.0;

        // Exponential height fog
        inscatter_sum *= exp(- surfacePos.z / GET_SETTING(Scattering, ground_fog_factor) );

        // Scale fog color
        vec4 fog_color = inscatter_sum * TimeOfDay.Scattering.fog_brightness;


        // Scale the fog factor after tinting the color, this reduces the ambient term
        // even more, this is a purely artistic choice
        fog_factor = saturate(fog_factor * 1.6);

        // Reduce sun factor, we don't want to have a sun disk shown trough objects
        inscatter = fog_color;
        sun_factor = 0;
    }


    // Apply inscattered light
    float phaseR = phaseFunctionR(nuStartPos);
    float phaseM = phaseFunctionM(nuStartPos);
    inscatteredLight = max(inscatter.rgb * phaseR + getMie(inscatter) * phaseM, 0.0f);

    // Sun disk
    vec3 silhouette_col = vec3(TimeOfDay.Scattering.sun_intensity) * inscatteredLight * fog_factor * sun_factor;
    float disk_factor = step(0.99995, dot(viewDir, sunVector));
    float outer_disk_factor = saturate(pow(max(0, dot(viewDir, sunVector)), 39200.0)) * 1.3;
    float upper_disk_factor = saturate( (viewDir.z - sunVector.z) * 0.3 + 0.01);
    outer_disk_factor = (exp(3.0 * outer_disk_factor) - 1) / (exp(4)-1);
    inscatteredLight += vec3(1,0.3,0.1) * disk_factor * 
        upper_disk_factor * 1e2 * 7.0 * silhouette_col;
    inscatteredLight += silhouette_col * outer_disk_factor * vec3(1, 0.8, 0.5) * 100.0;


    inscatteredLight *= 20.0;

    inscatteredLight *= saturate( (sunVector.z+0.1) * 40.0);

    return inscatteredLight;
}

