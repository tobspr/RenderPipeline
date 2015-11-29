

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
    // if (surfacePos.z < 0.0) {
    //     vec3 v2s = surfacePos - cameraPosition;
    //     float z_factor = abs(cameraPosition.z) / abs(v2s.z);
    //     surfacePos = cameraPosition + v2s * z_factor;
    //     viewDir = normalize(surfacePos - cameraPosition);
    // }

    vec3 inscatteredLight = vec3(0.0);
    float groundH = Rg + 0.5;
    float pathLength = distance(cameraPosition, surfacePos);
    vec3 startPos = cameraPosition;

    float height_scale_factor = 0.0;

    float startPosHeight = cameraPosition.z * height_scale_factor + groundH;
    float surfacePosHeight = surfacePos.z * height_scale_factor + groundH;

    float muStartPos = viewDir.z;
    float nuStartPos = max(0, dot(viewDir, sunVector));
    float musStartPos = sunVector.z;

    vec4 inscatter = max(texture4D(inscatterSampler, startPosHeight,
        muStartPos, musStartPos, nuStartPos), 0.0);
        
    fog_factor = 1.0;

    if(pathLength < 20000)
    {

        // Exponential height fog
        // float height_factor = saturate( exp( - (surfacePos.z)  / 160.0) );
        float height_factor = 1 - saturate( surfacePos.z / 560.0 );
        float fog_end = TimeOfDay.Scattering.fog_end;

        fog_factor = max(0, (1.0 - exp( -pathLength * viewDir.z / fog_end )) / viewDir.z);
        fog_factor *= height_factor;

        // Get atmospheric color
        vec4 inscatter_surf = texture4D(inscatterSampler, surfacePosHeight, 
            height_factor, musStartPos, nuStartPos);

        vec4 fog_color = fog_factor * inscatter_surf * TimeOfDay.Scattering.fog_brightness;
        fog_factor = saturate(fog_factor * 2.0);
        fog_color.w = inscatter_surf.w;
        inscatter = fog_color;
    }

    float phaseR = phaseFunctionR(nuStartPos);
    float phaseM = phaseFunctionM(nuStartPos);
    inscatteredLight = max(inscatter.rgb * phaseR + getMie(inscatter) * phaseM * 5.0, 0.0f);

    inscatteredLight *= sunIntensity * 1.0;


    // Sun disk
    float disk_factor = step(0.9996, dot(viewDir, sunVector));
    float upper_disk_factor = saturate( (viewDir.z - sunVector.z) * 0.3 + 0.01);

    inscatteredLight += vec3(1,0.3,0.0) * disk_factor * upper_disk_factor * 300.0 * TimeOfDay.Scattering.sun_color;

    // inscatteredLight = vec3(getMie(inscatter));



    return inscatteredLight;
}

