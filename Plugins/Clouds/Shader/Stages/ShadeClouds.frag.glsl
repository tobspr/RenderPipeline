#version 430

#define USE_MAIN_SCENE_DATA
#define USE_TIME_OF_DAY
#pragma include "Includes/Configuration.inc.glsl"
#pragma include "Includes/Noise.inc.glsl"

uniform sampler3D CloudVoxels;
uniform samplerCube ScatteringCubemap;
uniform writeonly image3D CloudVoxelsDest;

void main() {
    ivec2 coord_2d = ivec2(gl_FragCoord.xy);


    for (int z = 0; z < CLOUD_RES_Z; ++z) {

        ivec3 coord = ivec3(coord_2d, z);
        vec3 fcoord = coord / vec3(CLOUD_RES_XY, CLOUD_RES_XY, CLOUD_RES_Z);

        float cloud_factor = texelFetch(CloudVoxels, coord, 0).w;
        float height = float(z) / CLOUD_RES_Z; 
        vec3 cloud_color = vec3(1, 0.5, 0) * cloud_factor;

         vec3 sun_vector = -sun_azimuth_to_angle(
            TimeOfDay.Scattering.sun_azimuth,
            TimeOfDay.Scattering.sun_altitude);

        // Find cloud normal    
        vec3 nrm = vec3(0);
        for (int i = 1; i <= 4; i+=1) {
            int search_size = i;
            nrm += texelFetch(CloudVoxels, coord + search_size * ivec3( 0, 0, 1), 0).w * vec3( 0, 0,-1);
            nrm += texelFetch(CloudVoxels, coord + search_size * ivec3( 0, 0,-1), 0).w * vec3( 0, 0, 1);
            nrm += texelFetch(CloudVoxels, coord + search_size * ivec3( 0, 1, 0), 0).w * vec3( 0,-1, 0);
            nrm += texelFetch(CloudVoxels, coord + search_size * ivec3( 0,-1, 0), 0).w * vec3( 0, 1, 0);
            nrm += texelFetch(CloudVoxels, coord + search_size * ivec3( 1, 0, 0), 0).w * vec3(-1, 0, 0);
            nrm += texelFetch(CloudVoxels, coord + search_size * ivec3(-1, 0, 0), 0).w * vec3( 1, 0, 0);
        }
        nrm /= max(0.01, length(nrm));

        vec3 scattering_color = textureLod(ScatteringCubemap, nrm, 7).xyz;

        float cloud_brightness = max(0.1, 0.3 + 0.3 * dot(nrm, -sun_vector));

        // cloud_color = pow(scattering_color, vec3(1.0 / 2.2));

        // cloud_color *= max(0.2, dot(sun_vector, nrm)) * 2.0;
        // Tint clouds at the bottom
        // cloud_color += vec3(0, 0, 0.05) * max(0, -nrm.z);
        // Tint them at the top, too
        // cloud_color += vec3(0.1, 0, 0) * max(0, nrm.z);
        // cloud_color += vec3(0.1);
        // cloud_color = vec3(1);

        // Decrease cloud color at the bottom
        cloud_brightness *= 0.2 + max(0.0, height-0.15) * 1.1;
        // cloud_brightness = cloud_brightness * 16.0;


        cloud_color = vec3(scattering_color) * cloud_brightness;
        // cloud_color = vec3(cloud_brightness);
        cloud_color *= 5.0;
        cloud_color = cloud_color / (1.0 + cloud_color);

        // cloud_color = saturate(cloud_color);


        imageStore(CloudVoxelsDest, coord, vec4(cloud_color, cloud_factor));
    }
}
