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
    float sky_clip = 0.0;
    vec3 inscattered_light = DoScattering(m.position, view_vector, sky_clip)
                                * TimeOfDay.scattering.sun_intensity;
                            /* * TimeOfDay.scattering.sun_color * 0.01*/;
    
    result.xyz = textureLod(ShadedScene, texcoord, 0).xyz;
    result.w = 1;

    inscattered_light = srgb_to_rgb(inscattered_light);

    // Cloud color
    if (is_skybox(m)) {

        // #if !HAVE_PLUGIN(clouds)
            vec3 cloud_color = textureLod(DefaultSkydome, get_skydome_coord(view_vector), 0).xyz;
            cloud_color = pow(cloud_color, vec3(2.2));
            inscattered_light *= 0.0 + 1.0 * (0.7 + 2.6 * cloud_color);
        // #endif
        
        inscattered_light *= 3.0;
        inscattered_light *= 5.0;

        // Sun disk
        vec3 silhouette_col = vec3(TimeOfDay.scattering.sun_intensity) * inscattered_light * sky_clip;
        silhouette_col *= 2.0;
        float disk_factor = pow(saturate(dot(view_vector, sun_vector) + 0.000069), 23.0 * 1e5);
        float upper_disk_factor = smoothstep(0, 1, (view_vector.z + 0.045) * 1.0);
        inscattered_light += vec3(1,0.3,0.1) * disk_factor * upper_disk_factor * 2.0 * silhouette_col * 1.5 * 1e4;

    } else {
        inscattered_light *= 40.0;
        float dist = distance(m.position, MainSceneData.camera_pos);
        float extinction = exp(- dist / TimeOfDay.scattering.extinction); inscattered_light *= 0.5;

        #if !DEBUG_MODE
            result.xyz *= extinction;
            result.w = extinction;
        #endif
    }


    #if !DEBUG_MODE
        result.xyz += inscattered_light;
    #endif

    #if MODE_ACTIVE(SCATTERING)
        result.xyz = inscattered_light / (1 + inscattered_light);
    #endif

}
