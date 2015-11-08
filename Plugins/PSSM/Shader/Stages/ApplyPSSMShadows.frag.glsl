#version 400

#pragma include "Includes/Configuration.inc.glsl"
#pragma include "Includes/PositionReconstruction.inc.glsl"
#pragma include "Includes/GBufferPacking.inc.glsl"
#pragma include "Includes/LightingPipeline.inc.glsl"

out vec4 result;

// uniform vec3 cameraPosition;

uniform sampler2D GBufferDepth;
uniform sampler2D GBuffer0;
uniform sampler2D GBuffer1;
uniform sampler2D GBuffer2;
uniform sampler2D ShadedScene;

#if PSSM_USE_PCF
    uniform sampler2DShadow PSSMShadowAtlas;
#else
    uniform sampler2D PSSMShadowAtlas;
#endif

uniform float pssm_split_distance;
uniform int pssm_split_count;
uniform mat4 pssm_mvps[PSSM_NUM_SPLITS];


vec2 get_split_coord(vec2 local_coord, int split_index) {
    local_coord.x = (local_coord.x + split_index) / float(pssm_split_count);
    return local_coord;
}



void main() {

    vec3 sun_vector = normalize(vec3(0.05, 0.8, 0.4));
    vec3 sun_color = vec3(4, 4, 4);

    ivec2 coord = ivec2(gl_FragCoord.xy);
    float shadow_factor = 0.0;
    vec4 scene_color = texelFetch(ShadedScene, coord, 0);

    // Get the material
    Material m = unpack_material(GBufferDepth, GBuffer0, GBuffer1, GBuffer2);
    vec3 lighting_result = vec3(0);

    // Compute split index
    float depth = texelFetch(GBufferDepth, coord, 0).x;
    float linear_depth = getLinearZFromZ(depth);
    int split = int( log(1 + linear_depth / pssm_split_distance) * pssm_split_count);

    // Compute the shadowing factor
    if (split >= pssm_split_count) {
        if (is_skybox(m, cameraPosition)) {
            shadow_factor = 0.0;
        } else {
            shadow_factor = 1.0;
        }
    } else {
        mat4 mvp = pssm_mvps[split];

        vec4 projected = mvp * vec4(m.position, 1);
        projected.xyz /= projected.w;
        projected.xyz = fma(projected.xyz, vec3(0.5), vec3(0.5));

        vec2 projected_coord = get_split_coord(projected.xy, split);

        const float bias = 0.001;

        #if PSSM_USE_PCF
            float depth_value = texture(PSSMShadowAtlas, vec3(projected_coord, projected.z - bias));

        #else
            float depth_sample = texture(PSSMShadowAtlas, projected_coord, 0).x;
            float depth_value = step(projected.z - bias, depth_sample);
        #endif

        shadow_factor = depth_value;
    }

    // Compute the light influence
    vec3 v = normalize(cameraPosition - m.position);
    vec3 l = sun_vector;

    lighting_result = applyLight(m, v, l, sun_color, 1.0, shadow_factor);

    result = scene_color + vec4(lighting_result, 0);
}