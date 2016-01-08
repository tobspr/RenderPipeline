#version 430

#define USE_MAIN_SCENE_DATA
#define USE_TIME_OF_DAY
#pragma include "Includes/Configuration.inc.glsl"
#pragma include "Includes/Noise.inc.glsl"

uniform sampler3D CloudVoxels;
uniform samplerCube ScatteringCubemap;
uniform restrict writeonly image3D CloudVoxelsDest;
uniform sampler2D NoiseTex;

void main() {
    ivec2 coord_2d = ivec2(gl_FragCoord.xy);


    for (int z = 0; z < CLOUD_RES_Z; ++z) {

        ivec3 coord = ivec3(coord_2d, z);
        vec3 fcoord = (coord+0.5) / vec3(CLOUD_RES_XY, CLOUD_RES_XY, CLOUD_RES_Z);

        float cloud_factor = texelFetch(CloudVoxels, coord, 0).w;
        float height = float(z+0.5) / CLOUD_RES_Z; 
        vec3 cloud_color = vec3(1, 0.5, 0) * cloud_factor;

         vec3 sun_vector = -sun_azimuth_to_angle(
            TimeOfDay.Scattering.sun_azimuth,
            TimeOfDay.Scattering.sun_altitude);

        // Find cloud normal    
        vec3 nrm = vec3(0);
        vec3 pixel_size = 1.0 / vec3(CLOUD_RES_XY, CLOUD_RES_XY, CLOUD_RES_Z);
        for (int i = 1; i <= 6; i+=1) {
            nrm += textureLod(CloudVoxels, fcoord + i * pixel_size * vec3( 0, 0, 1), 0).w * vec3( 0, 0,-1);
            nrm += textureLod(CloudVoxels, fcoord + i * pixel_size * vec3( 0, 0,-1), 0).w * vec3( 0, 0, 1);
            nrm += textureLod(CloudVoxels, fcoord + i * pixel_size * vec3( 0, 1, 0), 0).w * vec3( 0,-1, 0);
            nrm += textureLod(CloudVoxels, fcoord + i * pixel_size * vec3( 0,-1, 0), 0).w * vec3( 0, 1, 0);
            nrm += textureLod(CloudVoxels, fcoord + i * pixel_size * vec3( 1, 0, 0), 0).w * vec3(-1, 0, 0);
            nrm += textureLod(CloudVoxels, fcoord + i * pixel_size * vec3(-1, 0, 0), 0).w * vec3( 1, 0, 0);
        }
        nrm /= max(0.1, length(nrm));

        vec3 noise = textureLod(NoiseTex, fcoord.xy * 16.0, 0).xyz * 2.0 - 1.0;
        // nrm = normalize(nrm + 0.1*noise);

        vec3 scattering_color = textureLod(ScatteringCubemap, nrm, 6).xyz;

        float cloud_brightness = 0.5 + 0.05 * dot(nrm, -sun_vector);

        // Decrease cloud color at the bottom
        cloud_brightness *= 0.2 + pow(height, 1.0) * 0.6;
        cloud_color = vec3(scattering_color) * cloud_brightness;

        cloud_color *= 15.0;
        cloud_color = cloud_color / (1.0 + cloud_color);

        // cloud_color = vec3(cloud_factor);
        // cloud_color *= cloud_factor;

        imageStore(CloudVoxelsDest, coord, vec4(cloud_color, cloud_factor));
    }
}
