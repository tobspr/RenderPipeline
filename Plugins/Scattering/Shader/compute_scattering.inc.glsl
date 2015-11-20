

// Include local scattering code
#define NO_COMPUTE_SHADER 1
#pragma include "scattering_common.glsl"

uniform sampler3D inscatterSampler;

float sunIntensity = TimeOfDay.Scattering.sun_intensity;
vec3 sunVector = sun_azimuth_to_angle(
        TimeOfDay.Scattering.sun_azimuth,
        TimeOfDay.Scattering.sun_altitude);


vec3 DoScattering(in vec3 surfacePos, in vec3 viewDir)
{

    // Move surface pos above ocean level
    if (surfacePos.z < 0.0) {
        vec3 v2s = surfacePos - cameraPosition;
        float z_factor = abs(cameraPosition.z) / abs(v2s.z);
        surfacePos = cameraPosition + v2s * z_factor;
        viewDir = normalize(surfacePos - cameraPosition);
    }

    vec3 inscatteredLight = vec3(0.0f, 0.0f, 0.0f);
    float groundH = Rg + 0.1;
    float pathLength = distance(cameraPosition, surfacePos);
    vec3 startPos = cameraPosition;

    float startPosHeight = (cameraPosition.z) * 0.01 + groundH;
    float surfacePosHeight = surfacePos.z * 0.01 + groundH;

    // Clamp start pos - this should usually not be required
    // startPosHeight = min(startPosHeight, Rt - 1);

    float muStartPos = viewDir.z;
    float nuStartPos = dot(viewDir, sunVector);
    float musStartPos = sunVector.z;

    vec4 inscatter = max(texture4D(inscatterSampler, startPosHeight,
        muStartPos, musStartPos, nuStartPos), 0.0f);

    float musEndPos = sunVector.z;

    if(pathLength < 30000 || viewDir.z < -0.0001)
    {
        // reduce total in-scattered light when surface hit
        // attenuation = analyticTransmittance(surfacePosHeight, surfacePos.z / Rt, 1.0);

        vec4 inscatterSurface = texture4D(inscatterSampler, surfacePosHeight, 
            0.0, musEndPos, nuStartPos);
        inscatterSurface *= saturate(pathLength / 25000.0);
        inscatter = inscatterSurface;
    }
    else
    {
        // retrieve extinction factor for inifinte ray
        // attenuation = analyticTransmittance(startPosHeight, muStartPos, pathLength);
    }

    float phaseR = phaseFunctionR(nuStartPos);
    float phaseM = phaseFunctionM(nuStartPos);
    inscatteredLight = max(inscatter.rgb * phaseR + getMie(inscatter) *
        phaseM, 0.0f);
    inscatteredLight *= sunIntensity;


    return inscatteredLight;
}

