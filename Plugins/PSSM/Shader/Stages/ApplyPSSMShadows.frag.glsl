#version 400

#pragma include "Includes/Configuration.inc.glsl"
#pragma include "Includes/PositionReconstruction.inc.glsl"
#pragma include "Includes/GBufferPacking.inc.glsl"
#pragma include "Includes/LightingPipeline.inc.glsl"
#pragma include "Includes/PoissonDisk.inc.glsl"
#pragma include "Includes/Shadows.inc.glsl"

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
uniform vec3 pssm_sun_vector;


vec2 get_split_coord(vec2 local_coord, int split_index) {
    local_coord.x = (local_coord.x + split_index) / float(pssm_split_count);
    return local_coord;
}



void main() {

    // TODO: Move to python
    vec3 sun_vector = normalize(pssm_sun_vector);
    vec3 sun_color = vec3(4, 4, 4);

    // Get current scene color
    ivec2 coord = ivec2(gl_FragCoord.xy);
    vec4 scene_color = texelFetch(ShadedScene, coord, 0);

    // Get the material data
    Material m = unpack_material(GBufferDepth, GBuffer0, GBuffer1, GBuffer2);

    // Variables to accumulate the shadows
    float shadow_factor = 0.0;
    vec3 lighting_result = vec3(0);

    // Compute split index
    float depth = texelFetch(GBufferDepth, coord, 0).x;
    float linear_depth = getLinearZFromZ(depth);
    int split = int( log(1 + linear_depth / pssm_split_distance) * pssm_split_count);


    // Compute the shadowing factor
    // If we are out of the PSSM range:    
    if (split >= pssm_split_count) {

        // If we have the skybox, just stop
        if (is_skybox(m, cameraPosition)) {
            result = scene_color;
            return;

        // Otherwise assume no shadows
        } else {
            shadow_factor = 1.0;
        }
    } else {

        // Get the MVP for the current split        
        mat4 mvp = pssm_mvps[split];

        // Project the current pixel to the view of the light
        vec3 projected = project(mvp, m.position);
        vec2 projected_coord = get_split_coord(projected.xy, split);

        // Do the actual filtering
        const float bias = 0.001;
        const int num_samples = 16;
        // const float filter_radius = 20.0 / PSSM_RESOLUTION;
        const float filter_radius = 20.0 / PSSM_RESOLUTION;

        // Find filter size
        vec2 filter_size = find_filter_size(mvp, sun_vector, filter_radius);


        for (int i = 0; i < num_samples; ++i) {

            vec2 offset = poisson_disk_2D_16[i] * filter_size;

            #if PSSM_USE_PCF
                float depth_value = texture(PSSMShadowAtlas, vec3(projected_coord + offset, projected.z - bias));
            #else
                float depth_sample = texture(PSSMShadowAtlas, projected_coord + offset, 0).x;
                float depth_value = step(projected.z - bias, depth_sample);
            #endif

            shadow_factor += depth_value;
        }

        shadow_factor /= num_samples;


    }

    // Compute the light influence
    vec3 v = normalize(cameraPosition - m.position);
    vec3 l = sun_vector;

    lighting_result = applyLight(m, v, l, sun_color, 1.0, shadow_factor);

    // lighting_result = vec3(shadow_factor);

    result = scene_color + vec4(lighting_result, 0);
}