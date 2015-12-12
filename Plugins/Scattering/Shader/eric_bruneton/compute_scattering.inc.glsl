

// Include local scattering code
#define NO_COMPUTE_SHADER 1
#pragma include "scattering_common.glsl"

uniform sampler3D InscatterSampler;

vec3 sun_vector = sun_azimuth_to_angle(
        TimeOfDay.Scattering.sun_azimuth,
        TimeOfDay.Scattering.sun_altitude);


vec3 DoScattering(vec3 surfacePos, vec3 viewDir, out float fog_factor)
{

    // Move surface pos above ocean level
    if (surfacePos.z < -0.01) {
        // vec3 v2s = surfacePos - cameraPosition;
        // float z_factor = abs(cameraPosition.z) / abs(v2s.z);
        // surfacePos = cameraPosition + v2s * z_factor;
        // viewDir = normalize(surfacePos - cameraPosition);
    }

    vec3 inscatteredLight = vec3(0.0);
    float groundH = Rg + 2.0;
    float pathLength = distance(cameraPosition, surfacePos);
    vec3 startPos = cameraPosition; 

    float height_scale_factor = 0.01;

    float startPosHeight = cameraPosition.z * height_scale_factor + groundH;
    float surfacePosHeight = surfacePos.z * height_scale_factor + groundH;

    float muStartPos = viewDir.z;
    float nuStartPos = max(0, dot(viewDir, sun_vector));
    float musStartPos = sun_vector.z;

    vec4 inscatter = max(texture4D(InscatterSampler, startPosHeight,
        muStartPos, musStartPos, nuStartPos), 0.0);
        
    fog_factor = 1.0;
    float sun_factor = 1.0; 

    if(pathLength < 20000)
    {

        // Exponential height fog
        float fog_ramp = TimeOfDay.Scattering.fog_ramp_size;
        float fog_start = TimeOfDay.Scattering.fog_start;

        // Exponential, I do not like the look
        // fog_factor = saturate((1.0 - exp( -pathLength * viewDir.z / fog_ramp )) / viewDir.z);

        // Looks better IMO
        fog_factor = smoothstep(0, 1, (pathLength-fog_start) / fog_ramp);
        // Produces a smoother transition, but the borders look weird then    
        // fog_factor = pow(fog_factor, 1.0 / 2.2);


        // Get atmospheric color, 3 samples should be enough
        const int num_samples = 3;

        float current_height = max(surfacePos.z, cameraPosition.z);

        current_height *= 1.0 - saturate(pathLength / 25000.0);

        float dest_height = surfacePos.z;
        float height_step = (dest_height - current_height) / num_samples;


        vec4 inscatter_sum = vec4(0);
        
        for (int i = 0; i < num_samples; ++i) {
            inscatter_sum += texture4D(InscatterSampler, 
                current_height * height_scale_factor + groundH, 
                current_height / 2400.0 + 0.001,
                musStartPos, nuStartPos);

            current_height += height_step;
        }

        inscatter_sum /= float(num_samples);
        inscatter_sum *= 0.5;

        // Exponential height fog
        inscatter_sum *= exp(- surfacePos.z / GET_SETTING(Scattering, ground_fog_factor) );

        // Scale fog color
        vec4 fog_color = inscatter_sum * TimeOfDay.Scattering.fog_brightness;

        fog_color *= fog_factor;

        // Scale the fog factor after tinting the color, this reduces the ambient term
        // even more, this is a purely artistic choice
        // fog_factor = saturate(fog_factor * 1.6);

        // Reduce sun factor, we don't want to have a sun disk shown trough objects
        float mix_factor = smoothstep(0, 1, (pathLength-10000.0) / 10000.0);
        inscatter = mix(fog_color, inscatter, mix_factor);
        sun_factor = 0;
    }


    // Apply inscattered light
    float phaseR = phaseFunctionR(nuStartPos);
    float phaseM = phaseFunctionM(nuStartPos);
    inscatteredLight = max(inscatter.rgb * phaseR + getMie(inscatter) * phaseM, 0.0f);

    inscatteredLight *= 60.0;

    inscatteredLight *= saturate( (sun_vector.z+0.1) * 40.0);

    return inscatteredLight;
}

