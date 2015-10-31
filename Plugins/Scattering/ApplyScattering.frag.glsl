#version 400

#pragma include "Includes/Configuration.inc.glsl"
#pragma include "Includes/GBufferPacking.inc.glsl"

// Include local scattering code
#define NO_COMPUTE_SHADER 1
#pragma include "Shader/scattering_common.glsl"

uniform sampler2D ShadedScene;

uniform sampler2D GBufferDepth;
uniform sampler2D GBuffer0;
uniform sampler2D GBuffer1;
uniform sampler2D GBuffer2;

uniform sampler3D inscatterSampler;

in vec2 texcoord;
out vec4 result;
uniform vec3 cameraPosition;

const float sunIntensity = 50.0;
const vec3 sunVector = normalize(vec3(0.1, 0.8, 0.01));

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

    if(pathLength < 30000 || viewDir.z < 0.0)
    {
        // reduce total in-scattered light when surface hit
        // attenuation = analyticTransmittance(surfacePosHeight, surfacePos.z / Rt, 1.0);

        vec4 inscatterSurface = texture4D(inscatterSampler, surfacePosHeight, 
            0.0, musEndPos, nuStartPos);
        inscatterSurface *= saturate(pathLength / 15000.0);
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

void main() {

    Material m = unpack_material(GBufferDepth, GBuffer0, GBuffer1, GBuffer2);
        
    vec3 view_vector = normalize(m.position - cameraPosition);
    vec3 scattering_result = vec3(0);

    vec3 inscattered_light = DoScattering(m.position, view_vector);


    // scattering_result = 1.0 - exp(-1.0 * inscatteredLight);

    if (is_skybox(m, cameraPosition) && m.position.z > 0.0) {
        vec3 cloud_color = m.diffuse;
        
        scattering_result = 1.0 - exp(-0.2 * inscattered_light);

        scattering_result += pow(cloud_color, vec3(1.2)) * 0.5;

    } else {
        scattering_result = 1.0 - exp(-0.2*inscattered_light);


    }

    result = texture(ShadedScene, texcoord);
    result.xyz += scattering_result;

}