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
#pragma include "render_pipeline_base.inc.glsl"
#pragma include "includes/gbuffer.inc.glsl"

uniform sampler2D ShadedScene;
uniform sampler2D DefaultSkydome;

uniform GBufferData GBuffer;

out vec4 result;

#pragma include "scattering_method.inc.glsl"

void main() {

    vec2 texcoord = get_texcoord();

    // Get material data
    Material m = unpack_material(GBuffer);
    vec3 view_vector = normalize(m.position - MainSceneData.camera_pos);

    // Fetch scattering
    float fog_factor = 0.0;
    vec3 inscattered_light = DoScattering(m.position, view_vector, fog_factor);
    inscattered_light *= TimeOfDay.scattering.sun_intensity
                            /* * TimeOfDay.scattering.sun_color * 0.01*/;


    // Cloud color
    if (is_skybox(m)) {
        #if !HAVE_PLUGIN(clouds)
            vec3 cloud_color = textureLod(DefaultSkydome, get_skydome_coord(view_vector), 0).xyz;
            cloud_color = cloud_color * vec3(1.0, 1, 0.9) * vec3(0.8, 0.7, 0.8524);
            cloud_color *= saturate(6.0 * (0.05 + view_vector.z));
            inscattered_light *= 0.0 + 1.2 * (0.3 + 0.6 * cloud_color);
        #endif

        // Sun disk
        vec3 silhouette_col = vec3(TimeOfDay.scattering.sun_intensity) * inscattered_light * fog_factor;
        silhouette_col *= 2.0;
        float disk_factor = pow(saturate(dot(view_vector, sun_vector) + 0.001), 30.0 * 1e4);
        float upper_disk_factor = smoothstep(0, 1, (view_vector.z + 0.045) * 1.0);
        inscattered_light += vec3(1,0.3,0.1) * disk_factor *
            upper_disk_factor * 2.0 * silhouette_col * 1.5 * 1e5;
    } else {
        inscattered_light *= 3.5;
        // inscattered_light *= 0.5;
    }


    // Mix with scene color
    result = textureLod(ShadedScene, texcoord, 0);


    #if !DEBUG_MODE
        result.xyz *= 1 - fog_factor;
        result.xyz += inscattered_light;
        result.w = fog_factor;
    #endif
}
