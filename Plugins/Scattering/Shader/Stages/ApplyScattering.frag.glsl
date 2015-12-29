#version 420

#define USE_MAIN_SCENE_DATA
#define USE_TIME_OF_DAY
#pragma include "Includes/Configuration.inc.glsl"
#pragma include "Includes/GBuffer.inc.glsl"

uniform sampler2D ShadedScene;
uniform sampler2D DefaultSkydome;

uniform GBufferData GBuffer;

in vec2 texcoord;
out vec4 result;

#pragma include "../ScatteringMethod.inc.glsl"

void main() {

    // Get material data
    Material m = unpack_material(GBuffer);
    vec3 view_vector = normalize(m.position - MainSceneData.camera_pos);

    // Fetch scattering
    float fog_factor = 0.0;
    vec3 inscattered_light = DoScattering(m.position, view_vector, fog_factor);

    // Cloud color
    if (is_skybox(m, MainSceneData.camera_pos) && view_vector.z > - MainSceneData.camera_pos.z * 0.0 - 0.025) {
        vec3 cloud_color = textureLod(DefaultSkydome, get_skydome_coord(view_vector), 0).xyz;
        inscattered_light += pow(cloud_color.y, 1.5) * TimeOfDay.Scattering.sun_intensity *
                                TimeOfDay.Scattering.sun_color * 2.0;

        // Sun disk
        vec3 silhouette_col = vec3(TimeOfDay.Scattering.sun_intensity) * inscattered_light * fog_factor;
        float disk_factor = step(0.99995, dot(view_vector, sun_vector));
        float upper_disk_factor = saturate( (view_vector.z - sun_vector.z) * 0.3 + 0.01);
        inscattered_light += vec3(1,0.3,0.1) * disk_factor * 
            upper_disk_factor * 7.0 * silhouette_col * 0.4 * 1e4;
    }
    
    // Mix with scene color
    result = textureLod(ShadedScene, texcoord, 0);
    
    #if !DEBUG_MODE
        result.xyz = mix(result.xyz, inscattered_light, fog_factor);
        result.w = fog_factor;
    #endif
}
