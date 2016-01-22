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

#version 420

#define USE_MAIN_SCENE_DATA
#define USE_TIME_OF_DAY
#pragma include "Includes/Configuration.inc.glsl"
#pragma include "Includes/GBuffer.inc.glsl"

uniform sampler2D ShadedScene;
uniform sampler2D DefaultSkydome;

uniform GBufferData GBuffer;

out vec4 result;

#pragma include "../ScatteringMethod.inc.glsl"

void main() {

    vec2 texcoord = get_texcoord();

    // Get material data
    Material m = unpack_material(GBuffer);
    vec3 view_vector = normalize(m.position - MainSceneData.camera_pos);

    // Fetch scattering
    float fog_factor = 0.0;
    vec3 inscattered_light = DoScattering(m.position, view_vector, fog_factor);

    // Cloud color
    if (is_skybox(m, MainSceneData.camera_pos)) {
        // vec3 cloud_color = textureLod(DefaultSkydome, get_skydome_coord(view_vector), 0).xyz;
        // inscattered_light += pow(cloud_color.y, 1.5) * TimeOfDay.Scattering.sun_intensity *
                                // TimeOfDay.Scattering.sun_color * 2.0;

        // Sun disk
        vec3 silhouette_col = vec3(TimeOfDay.Scattering.sun_intensity) * inscattered_light * fog_factor;
        float disk_factor = pow(max(0, dot(view_vector, sun_vector)), 40000.0);
        float upper_disk_factor = saturate( (view_vector.z - sun_vector.z) * 0.3 + 0.01);
        upper_disk_factor = smoothstep(0, 1, (view_vector.z + 0.01) * 30.0);
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
