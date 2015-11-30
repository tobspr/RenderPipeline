#version 400

#pragma include "Includes/Configuration.inc.glsl"
#pragma include "Includes/GBuffer.inc.glsl"

uniform sampler2D ShadedScene;
uniform sampler2D DefaultSkydome;

uniform GBufferData GBuffer;

in vec2 texcoord;
out vec4 result;

uniform vec3 cameraPosition;

#pragma include "../ScatteringMethod.inc.glsl"


void main() {

    // Get material data
    Material m = unpack_material(GBuffer);
    vec3 view_vector = normalize(m.position - cameraPosition);

    // Fetch scattering
    float fog_factor = 0.0;
    vec3 inscattered_light = DoScattering(m.position, view_vector, fog_factor);

    // Cloud color
    if (is_skybox(m, cameraPosition) && view_vector.z > - cameraPosition.z * 0.0 - 0.025) {
        vec3 cloud_color = textureLod(DefaultSkydome, get_skydome_coord(view_vector), 0).xyz;
        // inscattered_light += pow(cloud_color.y, 3.5) * TimeOfDay.Scattering.sun_intensity * 0.8;

        // Sun disk
        vec3 silhouette_col = vec3(TimeOfDay.Scattering.sun_intensity) * inscattered_light * fog_factor;
        float disk_factor = step(0.99998, dot(view_vector, sun_vector));
        float outer_disk_factor = saturate(pow(max(0, dot(view_vector, sun_vector)), 86200.0)) * 1.3;
        float upper_disk_factor = saturate( (view_vector.z - sun_vector.z) * 0.3 + 0.01);
        outer_disk_factor = (exp(3.0 * outer_disk_factor) - 1) / (exp(4)-1);
        inscattered_light += vec3(1,0.3,0.1) * disk_factor * 
            upper_disk_factor * 7.0 * silhouette_col;
        inscattered_light += silhouette_col * outer_disk_factor * vec3(1, 0.8, 0.5) * 100.0;
        
    }
    

    // Mix with scene color
    result = texture(ShadedScene, texcoord);
    result.xyz = mix(result.xyz, inscattered_light, fog_factor);
    result.w = fog_factor;

    // result.xyz = inscattered_light;
}
