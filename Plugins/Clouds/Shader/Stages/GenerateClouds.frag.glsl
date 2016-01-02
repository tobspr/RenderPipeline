#version 430

#define USE_MAIN_SCENE_DATA
#pragma include "Includes/Configuration.inc.glsl"
#pragma include "Includes/Noise.inc.glsl"

uniform writeonly image3D CloudVoxels;
uniform sampler2D NoiseTex;

float get_noise(vec3 c) {
    return snoise3D(c + 412) * 0.5 + 0.5;
}

float cloud_weight(float height) {
    // Clouds get less at higher distances. Also decrease them at the bottom
    const int border_pow = 2 * 2 + 1;
    // return 1.0;
    // Analytical formula, see wolframalpha: "-(2^15) * abs(x-0.5)^15 + 1 - 0.8*(x^2) from 0 to 1"
    return max(0, -pow(2, border_pow) * pow(abs(height - 0.5), border_pow) + 1.0 - 1.0 * pow(height, 4.0));

}

void main() {
    ivec2 coord = ivec2(gl_FragCoord.xy);

    vec2 flt_coord = vec2(coord) / CLOUD_RES_XY; 

    float time_offs = MainSceneData.frame_time * 0.01;
    vec3 wind_dir = vec3(0.8, 0.4, 0.01);
    vec3 wind_offset = time_offs * wind_dir * 1.0;

    for (int z = 0; z < CLOUD_RES_Z; ++z) {

        vec3 cloud_coord = vec3(flt_coord, float(z) / CLOUD_RES_Z);

        vec2 noise_coord = cloud_coord.xy * CLOUD_RES_XY / 128.0;

        float cloud_factor = 0.0;

        float f = 4.0;
        float a = 0.7;
        for (int i = 0; i < 4; ++i) {
            cloud_factor += get_noise(vec3(noise_coord, 0.0) * f + pow(f, 1.2) * wind_offset) * a;
            f *= 2.5;
            a *= 0.4;
        }

        float cloud_dense = 0.6 + 0.8 * cloud_coord.z;
        cloud_factor = cloud_factor * 1.8 - cloud_dense;
        cloud_factor *= cloud_weight(cloud_coord.z);
        cloud_factor = saturate(cloud_factor);

        imageStore(CloudVoxels, ivec3(coord, z), vec4(cloud_factor));
    }
}
