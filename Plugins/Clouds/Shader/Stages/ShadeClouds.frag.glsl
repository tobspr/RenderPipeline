/**
 * 
 * RenderPipeline
 * 
 * Copyright (c) 2014-2016 tobspr <tobias.springer1@gmail.com>
 * 
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 * 
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 * THE SOFTWARE.
 *
 */

#version 430

#define USE_MAIN_SCENE_DATA
#define USE_TIME_OF_DAY
#pragma include "Includes/Configuration.inc.glsl"
#pragma include "Includes/Noise.inc.glsl"

#pragma optionNV (unroll all)

flat in int instance_id;

uniform sampler3D CloudVoxels;
uniform samplerCube ScatteringIBLDiffuse;
uniform writeonly image3D RESTRICT CloudVoxelsDest;
uniform sampler2D NoiseTex;

void main() {

    ivec3 coord = ivec3(gl_FragCoord.xy, instance_id);
    vec3 fcoord = (coord+0.5) / vec3(CLOUD_RES_XY, CLOUD_RES_XY, CLOUD_RES_Z);

    float cloud_factor = texelFetch(CloudVoxels, coord, 0).w;
    float height = fcoord.z;
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

    vec3 scattering_color = texture(ScatteringIBLDiffuse, nrm).xyz;

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
